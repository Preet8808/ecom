# EcomOps - E-Commerce Microservices Platform

A production-grade DevOps Capstone Project demonstrating a complete CI/CD pipeline for a microservices-based e-commerce application using Flask, MongoDB, Docker, Kubernetes, Prometheus, and Grafana.

## Quick Start

### Option 1: Docker Compose (Local Development)

```bash
# Clone and start
git clone https://github.com/Preet8808/EcomOps.git
cd EcomOps
docker-compose up --build -d

# Access
# App: http://localhost:5000
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

### Option 2: Kubernetes (Minikube)

```bash
# Start Minikube
minikube start --driver=docker --cpus=4 --memory=6144

# Build images inside Minikube
eval $(minikube docker-env)
docker build -t preet8808/product-service:latest ./product-service
docker build -t preet8808/cart-service:latest ./cart-service
docker build -t preet8808/frontend:latest ./frontend

# Deploy everything
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/
kubectl apply -f monitoring/

# Access
minikube service frontend -n ecomops
minikube service grafana -n ecomops
```

## Architecture

```
User -> Frontend (NodePort 30080) -> Product Service (ClusterIP)
                                 -> Cart Service (ClusterIP)
                                         |
                                    MongoDB (ClusterIP + PVC)
                                         |
                              Prometheus (NodePort 30090) -> Grafana (NodePort 30300)
```

## Business Features

- **Product Catalog** - Full CRUD, search, filter, sort, pagination, reviews
- **Shopping Cart** - Add/remove items, quantity management
- **Coupon System** - 5 discount codes (SAVE10, SAVE20, WELCOME5, FREESHIP, FLASH25)
- **Shipping Tiers** - Standard ($5.99) / Express ($12.99), free over $75
- **Tax Calculation** - 8% automatic tax on post-discount subtotal
- **Checkout Flow** - Complete order processing with summary

## Services

| Service | Port | Type | Replicas |
|---------|------|------|----------|
| Frontend | 5000 | NodePort | 2 |
| Product Service | 5000 | ClusterIP | 2 |
| Cart Service | 5000 | ClusterIP | 2 |
| MongoDB | 27017 | ClusterIP | 1 |
| Prometheus | 9090 | NodePort | 1 |
| Grafana | 3000 | NodePort | 1 |

## Documentation

- **Complete Project Guide**: `Complete_Project_Guide.md` - Full architecture, setup, API reference
- **Git Bash Commands**: `GitBash_Command_Reference.md` - 300+ copy-paste commands
- **Gap Analysis**: `phase1-audit/Phase1_Gap_Analysis_Report.md`

## CI/CD Pipeline

```
Lint (flake8) -> Test (pytest) -> Build (Docker) -> Push (Docker Hub) -> Deploy (K8s)
```

Configure GitHub Secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `KUBE_CONFIG`

## Tech Stack

Python 3.11 | Flask | MongoDB 7.0 | Docker | Kubernetes | Prometheus | Grafana | GitHub Actions

## License

MIT License - Built for DevOps Capstone Project
