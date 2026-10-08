# Incident Tracker API

A small REST API for tracking production incidents (think: a lightweight
version of the incident logs I've kept manually during on-call and QA work),
built to practice a full CI/CD and Kubernetes deployment pipeline end to end.

## Why this project

I wanted something that mirrored the operational work I already do
(tracking incidents, severity, resolution status) but packaged as a real
service with the infrastructure around it that a production deployment
actually needs: tests, a CI pipeline, containerization, and a Kubernetes
deployment with health checks and autoscaling.

## Stack

- **API**: Python, Flask, Flask-SQLAlchemy
- **Database**: PostgreSQL (SQLite for local dev/tests)
- **Testing**: pytest, pytest-cov
- **Linting**: flake8
- **Containerization**: Docker, docker-compose
- **CI/CD**: GitHub Actions (lint, test, build image)
- **Orchestration**: Kubernetes manifests (Deployment, Service, HPA, health probes)

## API Endpoints

| Method | Endpoint              | Description                          |
|--------|------------------------|---------------------------------------|
| GET    | `/healthz`             | Health check (used by k8s probes)     |
| POST   | `/incidents`           | Create an incident                    |
| GET    | `/incidents`           | List incidents (filter by `status`, `severity`, `service`) |
| GET    | `/incidents/<id>`      | Get a single incident                 |
| PATCH  | `/incidents/<id>`      | Update status, severity, or description |
| DELETE | `/incidents/<id>`      | Delete an incident                    |
| GET    | `/incidents/stats`     | Counts by status and severity         |

## Running locally (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

python wsgi.py
# API now running on http://localhost:5000
```

## Running tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

21 tests covering create/list/get/update/delete, validation errors, filters,
and the stats endpoint.

## Running with Docker Compose

```bash
docker compose up --build
```

This starts a Postgres container and the API container together. The API
will be available at `http://localhost:5000`.



## Deploying to Kubernetes (minikube)

```bash
# Start a local cluster
minikube start

# Build the image inside minikube's Docker environment
eval $(minikube docker-env)
docker build -t incident-tracker-api:local .

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# HPA requires the metrics-server addon
minikube addons enable metrics-server
kubectl apply -f k8s/hpa.yaml

# Check everything is up
kubectl get pods -n incident-tracker
kubectl get hpa -n incident-tracker

# Access the API
kubectl port-forward -n incident-tracker svc/incident-tracker-api 5000:80
```

### What the Kubernetes setup actually does

- **Deployment**: runs 2 replicas of the API by default, with resource
  requests/limits so the scheduler knows what it needs
- **Liveness/readiness probes**: hit `/healthz` so Kubernetes can restart a
  stuck pod or stop routing traffic to one that isn't ready yet
- **HPA**: scales between 2 and 6 replicas based on CPU (70%) and memory
  (80%) utilization, with a 2-minute stabilization window on scale-down so
  it doesn't flap
- **Secret/ConfigMap**: database URL and config are injected via environment
  variables, not hardcoded

### Known simplification

Postgres uses `emptyDir` storage in `k8s/postgres.yaml`, which means data is
lost if the Postgres pod restarts. A real deployment would use a
`PersistentVolumeClaim` instead. I kept it simple here since the point of
this project is the API/CI/CD/K8s pipeline, not building a production
database setup, but it's worth knowing (and saying out loud in an
interview) that this is a deliberate simplification, not an oversight.

## CI/CD

GitHub Actions runs on every push and PR to `main`:
1. Install dependencies
2. Lint with flake8
3. Run the test suite with coverage
4. Build the Docker image (doesn't push anywhere, just confirms it builds)

See `.github/workflows/ci.yml`.

## What I'd add next

- PersistentVolumeClaim for Postgres instead of emptyDir
- Structured logging and a `/metrics` endpoint for Prometheus
- Push the built image to a real registry (Docker Hub or GHCR) in CI
- Ingress instead of port-forwarding for external access
