# Kubernetes — Local Setup Notes

Running the FastAPI app on Docker Desktop's Kubernetes. These are the exact steps
taken, in order, with the reasoning and the mistakes hit along the way.

Prereq: the Docker image exists locally.

```bash
docker build -t realtime-app:0.1.0 .
docker images | grep realtime-app     # confirm it's there
```

Enable Kubernetes in Docker Desktop (Settings → Kubernetes → Enable), then:

```bash
kubectl config current-context        # must say: docker-desktop
kubectl get nodes                     # one node, STATUS Ready
```

> `kubectl config current-context` matters. If it points at a different cluster,
> every command below silently targets the wrong place.

---

## Step 1 — Deployment: get a pod running

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods                      # STATUS should reach Running
```

### The file: `deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realtime-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: realtime-app        # <-- must match template labels below
  template:
    metadata:
      labels:
        app: realtime-app      # <-- stamped onto every pod created
    spec:
      containers:
        - name: realtime-app
          image: realtime-app:0.1.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
```

### Why each piece

**`kind: Deployment`** — you never create pods directly. You declare *desired state*
("1 pod running this image") and the Deployment controller continuously reconciles
reality to match. Delete a pod, it creates a replacement.

**`selector.matchLabels` must equal `template.metadata.labels`.** The Deployment
finds its pods by **label**, not by name. `template` is the cookie-cutter; `selector`
is how the Deployment recognises the cookies it made. Mismatch = manifest rejected.

**`imagePullPolicy: IfNotPresent`** — the local-only line. By default Kubernetes tries
to *pull* the image from a registry. Our image only exists in the local Docker daemon,
so a pull fails with `ErrImagePull`. `IfNotPresent` says "use the local copy."
**This is the line that changes for EKS**, once the image lives in ECR.

**`containerPort: 8000`** — where uvicorn listens inside the container.

### Verify / debug

```bash
kubectl get deployments               # READY 1/1
kubectl get pods
kubectl describe pod <pod-name>       # Events at the bottom say WHY it failed
kubectl logs <pod-name>               # uvicorn + our logger output
kubectl logs -l app=realtime-app      # select by label, no pod name needed
```

`kubectl logs` works because the app logs to **stdout** — that's the whole reason
the logger uses a `StreamHandler`. A log file inside the container would be invisible here.

At this point the app runs but is **unreachable**. A pod has no exposed address.

---

## Step 2 — Service: give the pods a stable address

Pods get ephemeral IPs that change on every restart. A Service is a stable front door.

```bash
kubectl apply -f k8s/service.yaml
kubectl get service realtime-app
kubectl get endpoints realtime-app    # THE check that matters — see below
```

### The file: `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: realtime-app
spec:
  type: LoadBalancer
  selector:
    app: realtime-app        # <-- matches the pod label from the Deployment
  ports:
    - name: http
      port: 8080             # port the Service answers on
      targetPort: 8000       # port on the container (uvicorn)
      protocol: TCP
```

### Why each piece

**The `selector` is the whole trick.** The Service knows no pod names or IPs. It says
"any pod labelled `app: realtime-app`, send traffic there." When a pod dies and the
Deployment makes a new one with a new IP, the Service picks it up automatically.
Loose coupling by label — the single most important idea in K8s networking.

**`port` vs `targetPort`** — the pair everyone mixes up:

```
client → Service:8080 → Pod:8000
          (port)        (targetPort)
```

They needn't match, and here deliberately don't.

**`type:`** only changes how traffic gets *in*. The routing-by-label is identical
across all three types:

| Type | Reachable from | Notes |
|------|---------------|-------|
| `ClusterIP` (default) | inside cluster only | a *virtual* IP; no machine owns it |
| `NodePort` | `localhost:30000-32767` | opens a port on the node itself |
| `LoadBalancer` | external | Docker Desktop → `localhost`; EKS → real AWS ELB |

They layer, they don't replace:

```
LoadBalancer  →  builds on NodePort  →  builds on ClusterIP  →  routes to Pods (by label)
```

You can see all three in one line of `kubectl get service` output:

```
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
realtime-app   LoadBalancer   10.110.138.178   localhost     8080:31234/TCP   1m
                              ^ClusterIP still ^LB door      ^auto NodePort
```

### Verify

```bash
curl http://localhost:8080/health      # {"status":"ok"}
# browser: http://localhost:8080/docs
kubectl logs -l app=realtime-app --tail=20   # confirm the request reached the pod
```

---

## Gotchas actually hit

**`kubectl get endpoints` shows `<none>`**
The Service's `selector` matches no pod labels. This is the #1 Service bug, and
`get endpoints` is how you catch it. `get service` looks perfectly healthy either way.

**Can't reach the `CLUSTER-IP` (e.g. `10.110.138.178`) from the laptop**
Correct and by design. A ClusterIP is a *virtual* IP — not on any network interface,
just iptables rules on the nodes. Docker Desktop's cluster runs in its own VM, so the
Windows host has no route to it. Prove the Service works from inside instead:

```bash
kubectl run tmp --rm -it --image=curlimages/curl --restart=Never -- \
  curl -s http://realtime-app/health
```

Use the **DNS name** (`realtime-app`), not the IP. Every Service gets an automatic
DNS record; the IP changes if the Service is recreated, the name never does.
In-cluster pod-to-pod traffic should always use the name.

**`ErrImagePull` / `ImagePullBackOff`**
Kubernetes tried to pull from a registry. Locally, fix with `imagePullPolicy: IfNotPresent`
and make sure the image tag exactly matches `docker images`.

**`port-forward` is a dev tool, not an access mechanism**
Fine for poking a `ClusterIP` service; not how anything reaches an app in production.

```bash
kubectl port-forward service/realtime-app 8080:80
```

---

## Everyday commands

```bash
kubectl apply -f k8s/                 # apply every manifest in the dir
kubectl get all                       # deployments, pods, services at a glance
kubectl describe pod <name>           # Events section = why it's broken
kubectl logs -f -l app=realtime-app   # follow logs by label
kubectl exec -it <pod> -- sh          # shell into the container
kubectl delete -f k8s/                # tear it all down
kubectl rollout restart deployment/realtime-app   # recreate pods (picks up new image)
```

Rebuilding the image does **not** update a running pod. Rebuild, then `rollout restart`.

---

## What changes when moving to EKS

Most of the above transfers unchanged — same YAML, same `kubectl`. The differences:

| Concern | Docker Desktop | EKS |
|---------|---------------|-----|
| Image source | local Docker daemon | must be pushed to **ECR**; nodes pull it |
| `imagePullPolicy` | `IfNotPresent` | `Always`, with immutable tags |
| `type: LoadBalancer` | faked → `localhost` | provisions a real AWS ELB (costs money, takes minutes) |
| Ingress | manual nginx install | AWS Load Balancer Controller |
| Nodes | one (the laptop) | real multi-node; resource requests/limits start mattering |
| Auth | just works | IAM + `aws eks update-kubeconfig`; IRSA for pod permissions |
| Log persistence | container filesystem, ephemeral | ship stdout → CloudWatch / Fluent Bit |

**Biggest trap:** locally you never push an image, so it's easy to write manifests that
silently depend on the image already being on the machine. On EKS that fails with
`ErrImagePull`.

**Use immutable tags** (`0.1.0`, `0.2.0` — never `latest`). If you overwrite a tag,
nodes may already have it cached and won't pull the update, so a rollout silently
deploys the old code.

---

## Next steps

- [ ] Liveness / readiness probes on `/health`
- [ ] Resource requests & limits
- [ ] `LOG_LEVEL` via ConfigMap / env var
- [ ] Push image to ECR
- [ ] Provision the EKS cluster and deploy