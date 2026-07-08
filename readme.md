# Realtime Application

A simple FastAPI application. Starting point for an eventual AWS EKS deployment.

## Endpoints

| Method | Path      | Description                         |
| ------ | --------- | ----------------------------------- |
| GET    | `/`       | Root greeting                       |
| GET    | `/health` | Health check (for K8s probes later) |
| POST   | `/echo`   | Echoes back a JSON `message`        |

Interactive API docs are auto-generated at `/docs` (Swagger UI) and `/redoc`.

## Run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell/CMD)
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the dev server (auto-reload on code changes)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs

## Quick test

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/echo -H "Content-Type: application/json" -d "{\"message\": \"hi\"}"
```

## Next steps

- [ ] Containerize with a Dockerfile
- [ ] Push image to Amazon ECR
- [ ] Kubernetes manifests (Deployment + Service)
- [ ] Provision EKS cluster and deploy
