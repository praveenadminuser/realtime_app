# Deploying to AWS — EKS + RDS Postgres

Step by step, with the AWS CLI. Assumes the app already runs locally against Postgres
(see [DATABASE.md](DATABASE.md)); this document is only about moving it to AWS.

> ## ⚠️ Read this before you start
>
> **This costs real money, roughly $150–250/month if you leave it running.** Approximate,
> region-dependent, and worth checking against the AWS pricing page rather than trusting
> these numbers:
>
> | Thing | Rough cost |
> |---|---|
> | EKS control plane | ~$73/mo — charged **per cluster, whether or not you run any pods** |
> | 2 × t3.medium nodes | ~$60/mo |
> | NAT gateway | ~$33/mo + data transfer (created by `eksctl` for private subnets) |
> | RDS db.t3.micro | ~$15/mo |
> | Network Load Balancer | ~$18/mo |
>
> There is **no free tier for the EKS control plane.** The meter starts the moment the
> cluster exists.
>
> **Go to [Teardown](#teardown) before you go to bed.** And read it first — deleting
> things in the wrong order orphans a load balancer that keeps billing you silently.

---

## The idea

Nothing about the *application* changes. [`app/config.py`](app/config.py) reads
`DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` and does not care who set
them. Moving to AWS is three substitutions:

| | Local Kubernetes | EKS |
|---|---|---|
| Image | local Docker daemon | **ECR** |
| Postgres | a pod (`k8s/postgres.yaml`) | **RDS** |
| Secret | committed YAML | **created from the CLI**, later Secrets Manager |

`k8s/service.yaml` doesn't change at all. `k8s/deployment.yaml` changes in exactly three
places (image URI, `imagePullPolicy`, `DB_SSL`).

---

## 0. Prerequisites

```bash
aws --version        # v2
eksctl version       # 0.190+
kubectl version --client
docker --version

aws configure        # the IAM user from the previous discussion
aws sts get-caller-identity      # confirm WHO you are — this identity matters, see step 3
```

`eksctl` is a CloudFormation wrapper. It does in one command what would otherwise be
~20 CLI calls (VPC, subnets, route tables, NAT gateway, IAM roles, node group). You could
do it all by hand with `aws ec2 ...`, and Terraform later will effectively make you.

### Set your variables once

Every command below reuses these. Keep this shell open.

```bash
export CLUSTER=realtime-eks
export REGION=eu-west-1                 # pick yours
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/realtime-app
export DB_MASTER_PASSWORD='ChangeMe-Str0ng-Passw0rd'    # never commit this
```

---

## 1. ECR — push the image

Nodes cannot see your laptop's Docker daemon. The image has to live somewhere they can
pull from.

```bash
# Create the registry
aws ecr create-repository \
  --repository-name realtime-app \
  --region $REGION \
  --image-scanning-configuration scanOnPush=true

# Authenticate Docker against it (the token lasts 12 hours)
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build, tag, push
docker build -t realtime-app:0.2.0 .
docker tag realtime-app:0.2.0 $ECR_REPO:0.2.0
docker push $ECR_REPO:0.2.0

# Confirm
aws ecr describe-images --repository-name realtime-app --region $REGION
```

**Immutable tags matter here.** Never push `latest`, and never overwrite `0.2.0` with
different code. Nodes cache images by tag — reuse a tag and a rollout can silently run the
*old* code on some nodes. Bump to `0.2.1` instead.

> If your laptop is Apple Silicon, add `--platform linux/amd64` to `docker build`, or the
> nodes will fail with `exec format error`. Not an issue on your Windows/amd64 machine.

---

## 2. Create the cluster

```bash
eksctl create cluster \
  --name $CLUSTER \
  --region $REGION \
  --version 1.31 \
  --nodegroup-name ng-default \
  --node-type t3.medium \
  --nodes 2 --nodes-min 2 --nodes-max 3 \
  --managed \
  --with-oidc
```

**This takes 15–20 minutes.** It is building a VPC, public and private subnets across
availability zones, a NAT gateway, route tables, the two IAM roles (cluster service role +
node instance role), the control plane, and a managed node group.

`--with-oidc` is not optional for you. It creates the OIDC identity provider that **IRSA**
needs — the mechanism that later lets a pod read Secrets Manager without static AWS keys.
Adding it afterwards is possible but annoying; just include it.

```bash
eksctl get cluster --region $REGION
kubectl get nodes                # 2 nodes, STATUS Ready
```

---

## 3. Confirm you can actually talk to the cluster

```bash
aws eks update-kubeconfig --name $CLUSTER --region $REGION
kubectl get svc                  # should show the built-in `kubernetes` ClusterIP
```

> **The single most common EKS wall.** The IAM principal that *creates* the cluster is
> silently granted Kubernetes admin, **and nobody else is**. Create the cluster as user A,
> run `kubectl` as user B, and you get:
>
> ```
> error: You must be logged in to the server (Unauthorized)
> ```
>
> That is *Kubernetes RBAC* refusing you, not IAM — so attaching more IAM policies will not
> fix it, which is what makes it so maddening. Use the **same identity** throughout. If you
> must grant another principal access:
>
> ```bash
> aws eks create-access-entry --cluster-name $CLUSTER --region $REGION \
>   --principal-arn arn:aws:iam::$ACCOUNT_ID:user/someone \
>   --type STANDARD
> aws eks associate-access-policy --cluster-name $CLUSTER --region $REGION \
>   --principal-arn arn:aws:iam::$ACCOUNT_ID:user/someone \
>   --access-scope type=cluster \
>   --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
> ```

---

## 4. RDS — the database

`k8s/postgres.yaml` is **not used on AWS.** Delete it from your mental model here. Running
a production database as a pod means owning backups, failover, patching and storage. RDS
exists so you don't.

### 4a. Find the network eksctl built

```bash
export VPC_ID=$(aws eks describe-cluster --name $CLUSTER --region $REGION \
  --query "cluster.resourcesVpcConfig.vpcId" --output text)

# The shared SG that eksctl attaches to the nodes — RDS will allow traffic FROM this.
export NODE_SG=$(aws eks describe-cluster --name $CLUSTER --region $REGION \
  --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" --output text)

# Private subnets only. A database must never sit in a public subnet.
export PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=*Private*" \
  --query "Subnets[].SubnetId" --output text)

echo "VPC=$VPC_ID  NODE_SG=$NODE_SG  SUBNETS=$PRIVATE_SUBNETS"
```

### 4b. Security group — the part that bites

```bash
export RDS_SG=$(aws ec2 create-security-group \
  --group-name realtime-rds-sg \
  --description "Postgres for realtime-app" \
  --vpc-id $VPC_ID \
  --query GroupId --output text)

# Allow 5432 FROM the node security group. Note --source-group, NOT --cidr:
# reference the SG by ID so it keeps working when node IPs change (they will).
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp --port 5432 \
  --source-group $NODE_SG
```

**Get this wrong and the symptom is a connection that HANGS and then times out — not one
that is refused.** A hang means a security group is dropping the packets. A *refusal* means
you have the endpoint or port wrong. That distinction will save you an hour.

### 4c. Create the instance

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name realtime-db-subnets \
  --db-subnet-group-description "Private subnets for realtime-app" \
  --subnet-ids $PRIVATE_SUBNETS

aws rds create-db-instance \
  --db-instance-identifier realtime-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.4 \
  --master-username appuser \
  --master-user-password "$DB_MASTER_PASSWORD" \
  --allocated-storage 20 \
  --db-name realtime \
  --vpc-security-group-ids $RDS_SG \
  --db-subnet-group-name realtime-db-subnets \
  --no-publicly-accessible \
  --storage-encrypted \
  --backup-retention-period 7

# ~5-10 minutes
aws rds wait db-instance-available --db-instance-identifier realtime-db

export RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier realtime-db \
  --query "DBInstances[0].Endpoint.Address" --output text)
echo $RDS_ENDPOINT
```

`--db-name realtime` matters: **RDS only creates a database if you name it here.** Omit it
and you get a running Postgres server with no `realtime` database, and Alembic fails with
`database "realtime" does not exist`. Neither RDS nor Alembic will create it for you.

`--no-publicly-accessible` means you cannot reach this from your laptop. That is correct
and deliberate. To poke at it, tunnel through a pod (see [Troubleshooting](#troubleshooting)).

---

## 5. Secrets Manager + External Secrets (IRSA)

The overlays expect the `postgres-credentials` Secret to be **created for them** by the
External Secrets Operator. Nobody types a password into a manifest, and nothing is committed.

```bash
kubectl create namespace dev

# 1. Store the credential in Secrets Manager, as separate fields.
#    Slash-delimited name so IAM can scope by prefix: secret:dev/*
aws secretsmanager create-secret \
  --name dev/realtime-app/db \
  --secret-string "{\"host\":\"$RDS_ENDPOINT\",\"port\":\"5432\",\"username\":\"appuser\",\"password\":\"$DB_MASTER_PASSWORD\",\"dbname\":\"realtime\"}"

# 2. Install the operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace

# 3. IRSA: an IAM role this namespace's ServiceAccount may assume, scoped to dev/* only.
#    eksctl writes the OIDC trust policy (pinning the sub claim) for you.
cat > /tmp/eso-dev-policy.json <<EOF
{"Version":"2012-10-17","Statement":[{
  "Effect":"Allow",
  "Action":"secretsmanager:GetSecretValue",
  "Resource":"arn:aws:secretsmanager:$REGION:$ACCOUNT_ID:secret:dev/*"
}]}
EOF
aws iam create-policy --policy-name eso-realtime-app-dev --policy-document file:///tmp/eso-dev-policy.json

eksctl create iamserviceaccount \
  --name external-secrets-dev \
  --namespace dev \
  --role-name eso-realtime-app-dev \
  --cluster $CLUSTER --region $REGION \
  --attach-policy-arn arn:aws:iam::$ACCOUNT_ID:policy/eso-realtime-app-dev \
  --approve --override-existing-serviceaccounts
```

Scope the policy to `secret:dev/*`, **not** the managed `SecretsManagerReadWrite` policy —
that grants read *and write* on every secret in the account. The whole point of separate
`dev/` `uat/` `prod/` names is that the dev role physically **cannot** read the prod credential.

> **The better move:** let RDS own the password entirely. Add `--manage-master-user-password`
> to `create-db-instance` in step 4c and AWS generates it, stores it in Secrets Manager in
> exactly this JSON shape, and **rotates it** — you never see or handle it at all.

### How ESO actually gets AWS credentials — there is no access key

The `serviceaccount.yaml` in each overlay carries one annotation:
`eks.amazonaws.com/role-arn`. That is the entire mechanism:

1. EKS's admission webhook sees the annotation and injects into the pod a **short-lived JWT
   signed by the cluster** (at `/var/run/secrets/eks.amazonaws.com/serviceaccount/token`),
   plus `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE`.
2. The AWS SDK inside ESO finds those on its own and calls `sts:AssumeRoleWithWebIdentity`.
3. STS verifies the JWT against the cluster's OIDC provider (that's what `--with-oidc`
   registered in step 2) and checks the role's trust policy, which pins the token's `sub`
   claim to `system:serviceaccount:dev:external-secrets-dev`.
4. STS returns temporary credentials (~1h, auto-refreshed). ESO calls `GetSecretValue`,
   maps the five JSON fields, and writes the Kubernetes Secret.

**No AWS access key exists anywhere in that chain.** The pod's identity is its
ServiceAccount, proven cryptographically. A pod in another namespace cannot assume the
role — not "shouldn't", *can't*.

---

## 6. Point the manifests at AWS

**You do not edit any manifest.** That's the job of the Kustomize overlays:

```
k8s/
  base/                    deployment, service, migration-job — environment-agnostic
  overlays/
    local/                 Docker Desktop + in-cluster Postgres
    dev/  uat/  prod/      EKS + RDS + External Secrets
```

Each overlay patches only what genuinely differs:

| | local | dev / uat / prod |
|---|---|---|
| image | `realtime-app:0.2.0` (local daemon) | `<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/realtime-app:0.2.0` |
| `imagePullPolicy` | `IfNotPresent` | `Always` |
| `DB_SSL` | `false` | `true` — RDS refuses plaintext |
| replicas | 1 | 2 / 2 / 3 |
| Postgres | a pod (`postgres.yaml`) | **absent** — it's RDS |
| Secret | committed YAML | created by **External Secrets** from Secrets Manager |

`base/deployment.yaml` never changes, because it names the Secret rather than its
contents. Hand-editing manifests between environments is how a production ECR URI ends
up committed on a local branch — the overlay makes that impossible.

**One-time setup:** replace `<ACCOUNT_ID>` and `<REGION>` in `k8s/overlays/dev/`
(`kustomization.yaml`, `serviceaccount.yaml`, `secretstore.yaml`), and the same in
`uat/` and `prod/`.

Preview exactly what will be applied, before applying it:

```bash
kubectl kustomize k8s/overlays/dev        # renders to stdout; applies nothing
```

---

## 7. Deploy

One command applies the namespace, ServiceAccount, SecretStore, ExternalSecret,
Deployment, Service and migration Job — all into the `dev` namespace:

```bash
kubectl delete job db-migrate -n dev --ignore-not-found   # Jobs are immutable
kubectl apply -k k8s/overlays/dev
```

**Check the Secret actually materialised before anything else.** This is the step most
likely to fail, and every later symptom traces back to it:

```bash
kubectl get externalsecret -n dev          # STATUS should be SecretSynced
kubectl get secret postgres-credentials -n dev
kubectl describe externalsecret postgres-credentials -n dev   # Events name the IAM failure
```

If it says `SecretSyncedError`, the IRSA role or its trust policy is wrong — go back to
step 9. No amount of restarting pods will fix it.

Then the migration, which must complete before the app serves a request:

```bash
kubectl wait --for=condition=complete job/db-migrate -n dev --timeout=300s
kubectl logs job/db-migrate -n dev
# expect: Running upgrade -> 0001, initial messages table
#         Running upgrade 0001 -> 0002, add users table
```

If that Job cannot reach RDS, **stop here and fix it.** Deploying the app on a broken
database just moves the error somewhere less legible.

```bash
kubectl rollout status deployment/realtime-app -n dev
kubectl get pods -n dev
```

---

## 8. Verify

```bash
# The ELB hostname. Takes 2-3 minutes to appear, and a further ~60s to pass health checks.
export APP_URL=$(kubectl get svc realtime-app -n dev \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo http://$APP_URL:8080

curl http://$APP_URL:8080/health          # {"status":"ok"}          — liveness, no DB
curl http://$APP_URL:8080/health/ready    # {"status":"ready",...}   — proves RDS is reachable

curl -X POST http://$APP_URL:8080/messages \
  -H "Content-Type: application/json" -d '{"body":"hello from EKS"}'
curl http://$APP_URL:8080/messages
```

`/health/ready` returning `{"database":"ok"}` is the moment the whole chain is proven:
pod → ExternalSecret → IRSA → Secrets Manager → Secret → security group → RDS → TLS.

A pod stuck at `0/1 Running` with **zero restarts** is the readiness probe doing its job —
the process is alive but cannot reach RDS. Don't disable the probe; read the logs:

```bash
kubectl get pods -n dev                              # READY column
kubectl get endpoints realtime-app -n dev            # not-ready pods are absent here
kubectl logs -l app=realtime-app -n dev --prefix -f --tail=50
```

---

## 9. Promoting to uat and prod

Repeat steps 4, 5 and 7 with the environment name swapped. Nothing else changes — the
overlays already exist:

```bash
# per environment: its own RDS instance, its own Secrets Manager entry,
# its own IRSA role scoped to that prefix, its own namespace
aws secretsmanager create-secret --name prod/realtime-app/db --secret-string '{...}'
eksctl create iamserviceaccount --name external-secrets-prod --namespace prod ...
kubectl apply -k k8s/overlays/prod
```

The application code, the Dockerfile, the image, and `k8s/base/` are **byte-for-byte
identical** across all three. The only things that vary are the Secret's contents, the
image tag, and the replica count.

### The rotation caveat — read this one

**Environment variables are frozen when a container starts.** When Secrets Manager rotates
the password and ESO refreshes the Kubernetes Secret, your **running pods keep the old
value** and fail on their next reconnect — not immediately, which makes it a confusing 3am
failure.

Either `kubectl rollout restart deployment/realtime-app -n prod` after a rotation, or
install [Reloader](https://github.com/stakater/Reloader), which watches the Secret and rolls
the Deployment for you. This is the main wart of the env-var approach; the Secrets Store CSI
driver (which mounts secrets as *files* that update in place) is the structural fix, at the
cost of changing `app/config.py` to read a file.

### Prod belongs somewhere else

Namespaces isolate **names**, not blast radius. A stray `kubectl apply -k
k8s/overlays/prod` still lands on the same control plane, and a node problem hits every
namespace on it. dev and uat sharing a cluster is normal; **prod should be a separate
cluster, ideally a separate AWS account.** Then `prod/realtime-app/db` lives somewhere your
dev cluster holds no credentials for at all — a wall, rather than a guardrail.

---

## Teardown

**Do this in order.** The order is not cosmetic.

```bash
# 1. DELETE THE SERVICE FIRST.
#    `type: LoadBalancer` provisioned a real AWS load balancer. Deleting the Kubernetes
#    Service is what tears it down. Delete the CLUSTER first and the ELB is orphaned —
#    it survives, it is invisible in the EKS console, and it keeps billing you.
kubectl delete -k k8s/overlays/dev        # Service, Deployment, Job, ExternalSecret, namespace

# 2. RDS. --skip-final-snapshot is FINE HERE (learning project) and CATASTROPHIC anywhere real.
aws rds delete-db-instance \
  --db-instance-identifier realtime-db \
  --skip-final-snapshot --delete-automated-backups
aws rds wait db-instance-deleted --db-instance-identifier realtime-db
aws rds delete-db-subnet-group --db-subnet-group-name realtime-db-subnets

# 3. The cluster (~10-15 min). This also removes the VPC, NAT gateway and node group.
eksctl delete cluster --name $CLUSTER --region $REGION

# 4. The rest
aws ecr delete-repository --repository-name realtime-app --region $REGION --force
aws secretsmanager delete-secret --secret-id prod/realtime-app/db --force-delete-without-recovery
```

Then **check the console** — `eksctl delete cluster` fails if the VPC still has
dependencies (an orphaned ELB is the usual culprit, which is why step 1 comes first):

```bash
aws elbv2 describe-load-balancers --region $REGION --query "LoadBalancers[].LoadBalancerName"
aws ec2 describe-vpcs --region $REGION --query "Vpcs[?Tags[?Value=='$CLUSTER']].VpcId"
```

Neither should return anything related to this project. **Check your billing dashboard the
next day.**

---

## Troubleshooting

**`ImagePullBackOff`**
The node role lacks `AmazonEC2ContainerRegistryReadOnly`, or the image URI/tag is wrong.
`kubectl describe pod <name>` — the Events at the bottom name the actual failure.

**Migration Job hangs, then times out**
Security group. `$RDS_SG` must allow inbound 5432 from `$NODE_SG`. A *hang* is a dropped
packet; a *refusal* is the wrong endpoint or port.

**`database "realtime" does not exist`**
You omitted `--db-name realtime` when creating the RDS instance. RDS made a server, not a
database.

**`sslmode is an invalid keyword argument`**
Someone put `?sslmode=require` in a URL. asyncpg does not speak libpq's parameter — that's
what `DB_SSL=true` is for. See [`app/db.py`](app/db.py).

**TLS certificate verification failure against RDS**
`ssl.create_default_context()` uses the system trust store. If your RDS certificate doesn't
chain to a root that's in it, download the RDS bundle, mount it into the pod, and build the
context from it (`cafile=`):
```bash
curl -O https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
kubectl create configmap rds-ca --from-file=global-bundle.pem
```

**`FATAL: too many connections`**
`(db_pool_size + db_max_overflow) × replicas` exceeded the instance's `max_connections` —
a db.t3.micro allows only ~87. Do that multiplication before scaling. Shrink the pool, or
put **RDS Proxy** in front and point `DB_HOST` at the proxy.

**Reach RDS from your laptop (it's private, by design)**
```bash
kubectl run pg --rm -it --image=postgres:16-alpine --restart=Never -- \
  psql "postgresql://appuser:$DB_MASTER_PASSWORD@$RDS_ENDPOINT:5432/realtime?sslmode=require"
```
Note this one *does* use `sslmode` — that's `psql`, which is libpq and understands it.
Your app is asyncpg, which does not. Same database, two different client libraries.

---

## Doing this in Terraform (later)

Everything above is **imperative** — a sequence of commands whose result lives only in your
AWS account and your shell history. Re-creating it means re-running them in order and hoping
you remember the flags. That's exactly the problem Terraform solves: the same infrastructure
becomes a *declared* state in files you commit, diff, and review.

The mapping is close to one-to-one:

| This document | Terraform |
|---|---|
| `eksctl create cluster` | `terraform-aws-modules/eks/aws` |
| `aws ec2 create-security-group` + ingress | `aws_security_group` + `aws_security_group_rule` |
| `aws rds create-db-instance` | `terraform-aws-modules/rds/aws` |
| `aws ecr create-repository` | `aws_ecr_repository` |
| `aws secretsmanager create-secret` | `aws_secretsmanager_secret` + `..._version` |
| `eksctl create iamserviceaccount` | `aws_iam_role` + `aws_iam_role_policy_attachment` with an OIDC trust policy |
| `kubectl apply -f` | **keep using kubectl/Kustomize** — see below |

Three things worth knowing before you start:

**Use the community modules, not raw resources.** `terraform-aws-modules/eks/aws` is what
`eksctl` is doing under the hood, and hand-rolling a VPC + node group + IRSA from primitives
is a genuinely large job.

**Don't manage Kubernetes objects with Terraform.** The `kubernetes` provider *can* apply
Deployments, and it's a common regret: Terraform's state model fits slow-moving cloud
infrastructure, not objects you redeploy ten times a day. Draw the line at the cluster —
Terraform owns AWS, `kubectl`/Kustomize/Helm owns what runs inside it.

**Do this *after* you've done it by hand.** The CLI path above teaches you what the
resources are and how they connect. Terraform then removes the tedium. Starting with
Terraform means debugging a module abstraction over services you've never seen, which is a
much harder first lesson.

---

## What is verified here

Honest disclosure: the local Docker Compose path in [DATABASE.md](DATABASE.md) has been run
end to end. **Everything in this document has not** — it was not executed against a live AWS
account. The commands and their ordering are sound, but expect to hit at least one thing
(an IAM permission, an engine version that's no longer offered, a flag renamed between CLI
versions). Read the error, don't just re-run.
