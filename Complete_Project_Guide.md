# EcomOps - Complete Project Guide
## DevOps Capstone Project: E-Commerce Microservices Platform

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Business Logic & Features](#3-business-logic--features)
4. [Project Structure](#4-project-structure)
5. [Technology Stack](#5-technology-stack)
6. [Prerequisites](#6-prerequisites)
7. [Step-by-Step Setup Guide](#7-step-by-step-setup-guide)
8. [Running with Docker Compose](#8-running-with-docker-compose)
9. [Kubernetes Deployment](#9-kubernetes-deployment)
10. [Monitoring Setup](#10-monitoring-setup)
11. [CI/CD Pipeline Configuration](#11-cicd-pipeline-configuration)
12. [API Reference](#12-api-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [Production Considerations](#14-production-considerations)

---

## 1. PROJECT OVERVIEW

### What is EcomOps?

**EcomOps** is a production-grade, microservices-based e-commerce platform designed as a **DevOps Capstone Project**. It demonstrates the complete lifecycle of a modern cloud-native application: from code to container to cluster, with full observability and automated deployment.

### What Makes This Project Unique?

Unlike typical tutorial projects, EcomOps implements **real business logic** with enterprise patterns:

- **Coupon System** with percentage/fixed/shipping discounts and minimum order thresholds
- **Dynamic Pricing** with tax calculation, shipping tiers, and discount stacking
- **Review & Rating System** with weighted average calculation
- **Soft Delete Pattern** for data integrity
- **Cart Expiration** with automatic cleanup capability
- **Multi-environment Configuration** via ConfigMaps and Secrets

### Project Goals

| Goal | Status |
|------|--------|
| Microservices architecture with service discovery | Complete |
| Containerization with Docker & multi-stage builds | Complete |
| Local orchestration with Docker Compose | Complete |
| Kubernetes deployment with health probes | Complete |
| Automated CI/CD with GitHub Actions | Complete |
| Monitoring with Prometheus metrics | Complete |
| Visualization with Grafana dashboards | Complete |
| Unit testing with pytest | Complete |
| Production security best practices | Complete |

---

## 2. ARCHITECTURE DEEP DIVE

### System Architecture Diagram

```
                    +------------------+
                    |    End User      |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Load Balancer  |
                    |  (NodePort 30080)|
                    +--------+---------+
                             |
              +--------------v--------------+
              |         ecomops NS          |
              |  +----------------------+   |
              |  |     Frontend SVC     |   |
              |  |    (2 replicas)      |   |
              |  |   Flask + Jinja2     |   |
              |  +--+---------------+---+   |
              |     |               |       |
              |  +--v---------+  +--v----+   |
              |  |Product SVC |  |Cart   |   |
              |  | (2 replicas)|  |SVC    |   |
              |  | Flask +     |  |(2 rep)|   |
              |  | MongoDB     |  |Flask  |   |
              |  +--+---------+  +--+----+   |
              |     |               |       |
              |  +--v---------------v---+   |
              |  |     MongoDB SVC       |   |
              |  |   (1 replica + PVC)   |   |
              |  +-----------------------+   |
              |                              |
              |  +----------+  +---------+   |
              |  |Prometheus|  | Grafana |   |
              |  | NodePort |  | NodePort|   |
              |  |  30090   |  |  30300  |   |
              |  +----------+  +---------+   |
              +------------------------------+
```

### Data Flow

1. **User** accesses the frontend via NodePort (or Ingress in production)
2. **Frontend** renders HTML templates and calls backend services via internal DNS
3. **Product Service** handles product CRUD, search, filtering, reviews
4. **Cart Service** manages shopping carts, applies coupons, processes checkout
5. **MongoDB** persists all data with PersistentVolume for durability
6. **Prometheus** scrapes /metrics from all services every 15s
7. **Grafana** visualizes collected metrics on pre-built dashboards

### Inter-Service Communication

| From | To | Method | URL |
|------|-----|--------|-----|
| Frontend | Product Service | HTTP GET/POST | `http://product-service.ecomops.svc.cluster.local:5000` |
| Frontend | Cart Service | HTTP GET/POST/PUT/DELETE | `http://cart-service.ecomops.svc.cluster.local:5000` |
| Cart Service | Product Service | HTTP GET | `http://product-service.ecomops.svc.cluster.local:5000/products` |
| Prometheus | All Services | HTTP GET | `:5000/metrics` |

---

## 3. BUSINESS LOGIC & FEATURES

### Product Catalog Service

| Feature | Description |
|---------|-------------|
| Full CRUD | Create, read, update, soft-delete products |
| Auto SKU Generation | Generates SKU if not provided (PRD-YYYYMMDDhhmmss) |
| Search | Full-text search across name and description |
| Filter | By category, brand, price range |
| Sort | By price, name, rating, date |
| Pagination | Configurable page size (default 20, max 100) |
| Reviews | Add star ratings (1-5) with comments |
| Rating Aggregation | Automatic average rating recalculation |

### Cart Service

| Feature | Description |
|---------|-------------|
| Cart Lifecycle | Create, expire (48h), checkout, delete |
| Item Management | Add, update quantity, remove |
| 5 Coupon Types | SAVE10, SAVE20, WELCOME5, FREESHIP, FLASH25 |
| Discount Logic | Percentage off, fixed amount off, free shipping |
| Minimum Orders | Each coupon has required minimum cart value |
| Shipping Tiers | Standard ($5.99) vs Express ($12.99) |
| Free Shipping | Automatic on orders over $75 |
| Tax Calculation | 8% tax on subtotal after discounts |
| Order Summary | Complete checkout with payment method capture |

### Frontend

| Feature | Description |
|---------|-------------|
| Responsive Design | Mobile-first, works on all screen sizes |
| AJAX Cart | Add/remove items without page reload |
| Live Cart Count | Updates cart badge in real-time |
| Coupon Selection | Click-to-apply coupon tags |
| Shipping Selection | Toggle between standard and express |
| Checkout Flow | Step-by-step with order confirmation |

---

## 4. PROJECT STRUCTURE

```
EcomOps/
|-- product-service/
|   |-- app.py              # Flask app with full CRUD
|   |-- Dockerfile          # Multi-stage build
|   |-- requirements.txt    # Flask, PyMongo, prometheus
|
|-- cart-service/
|   |-- app.py              # Flask app with cart logic
|   |-- Dockerfile          # Multi-stage build
|   |-- requirements.txt    # Flask, PyMongo, requests
|
|-- frontend/
|   |-- app.py              # Flask app serving HTML UI
|   |-- templates/          # Jinja2 HTML templates
|   |   |-- base.html       # Master layout template
|   |   |-- index.html      # Homepage with featured products
|   |   |-- products.html   # Product listing with filters
|   |   |-- product_detail.html  # Single product view
|   |   |-- cart.html       # Shopping cart page
|   |   |-- checkout_success.html  # Order confirmation
|   |   |-- error.html      # Error page template
|   |-- Dockerfile          # Multi-stage build
|   |-- requirements.txt    # Flask, requests
|
|-- tests/
|   |-- __init__.py
|   |-- test_product_service.py  # 15+ unit tests
|   |-- test_cart_service.py     # 15+ unit tests
|
|-- k8s/                    # Kubernetes manifests
|   |-- namespace.yaml
|   |-- secrets.yaml
|   |-- configmap.yaml
|   |-- mongodb-deployment.yaml
|   |-- mongodb-service.yaml
|   |-- product-deployment.yaml
|   |-- product-service.yaml
|   |-- cart-deployment.yaml
|   |-- cart-service.yaml
|   |-- frontend-deployment.yaml
|   |-- frontend-service.yaml
|
|-- monitoring/             # Prometheus + Grafana
|   |-- prometheus.yml
|   |-- prometheus-deployment.yaml
|   |-- prometheus-service.yaml
|   |-- grafana-deployment.yaml
|   |-- grafana-service.yaml
|
|-- .github/workflows/
|   |-- ci-cd.yml           # Complete CI/CD pipeline
|
|-- docker-compose.yml      # Local development
|-- Complete_Project_Guide.md    # This document
|-- GitBash_Command_Reference.md # All commands
|-- README.md               # Quick start
```

---

## 5. TECHNOLOGY STACK

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11 | Application code |
| **Framework** | Flask | Web microframework |
| **Database** | MongoDB 7.0 | Document store |
| **ODM** | Flask-PyMongo | MongoDB integration |
| **Containers** | Docker | Application packaging |
| **Orchestration** | Kubernetes | Container orchestration |
| **Local Dev** | Docker Compose | Multi-container local dev |
| **CI/CD** | GitHub Actions | Automated pipeline |
| **Metrics** | Prometheus | Time-series database |
| **Dashboards** | Grafana | Visualization |
| **Exporter** | prometheus-flask-exporter | Flask metrics |
| **Testing** | pytest | Unit testing |
| **Cluster** | Minikube | Local Kubernetes |

---

## 6. PREREQUISITES

### Required Software

| Tool | Minimum Version | Install Command |
|------|----------------|-----------------|
| Git | 2.30+ | `apt install git` / `brew install git` |
| Docker | 24.0+ | [docker.com/get-started](https://docker.com/get-started) |
| Docker Compose | 2.20+ | Included with Docker Desktop |
| kubectl | 1.28+ | `apt install kubectl` / `brew install kubectl` |
| Minikube | 1.32+ | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io) |
| Python | 3.11+ | `apt install python3.11` / `brew install python@3.11` |

### Verify Installations

```bash
git --version
docker --version
docker-compose version
kubectl version --client
minikube version
python3 --version
```

### GitHub Repository Setup

1. Create a Docker Hub account at [hub.docker.com](https://hub.docker.com)
2. Generate an access token in Docker Hub Account Settings > Security
3. Fork/clone the repository: `git clone https://github.com/Preet8808/EcomOps.git`

---

## 7. STEP-BY-STEP SETUP GUIDE

### Step 1: Clone the Repository

```bash
git clone https://github.com/Preet8808/EcomOps.git
cd EcomOps
```

### Step 2: Verify Project Structure

```bash
# List all directories and key files
tree -L 2 -d
ls -la */*.py
ls k8s/
ls monitoring/
```

Expected output: All directories (product-service, cart-service, frontend, k8s, monitoring, tests) should exist.

### Step 3: Build and Run with Docker Compose (Local Development)

```bash
# Build all images and start services
docker-compose up --build -d

# Verify all containers are running
docker-compose ps

# Check logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f product-service
docker-compose logs -f cart-service
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Step 4: Access the Application (Docker Compose)

| Service | URL | Description |
|---------|-----|-------------|
| Frontend App | http://localhost:5000 | Main e-commerce UI |
| Product API | http://localhost:5001 | Product service endpoint |
| Cart API | http://localhost:5002 | Cart service endpoint |
| Prometheus | http://localhost:9090 | Metrics dashboard |
| Grafana | http://localhost:3000 | Visualization (admin/admin123) |
| MongoDB | localhost:27017 | Database (admin/password123) |

### Step 5: Seed Sample Data

```bash
# Access MongoDB and insert sample products
docker-compose exec mongodb mongosh -u admin -p password123 --authenticationDatabase admin ecomops
```

In the MongoDB shell:
```javascript
db.products.insertMany([
  { name: "Wireless Headphones", sku: "ELEC-001", description: "Premium noise-cancelling headphones", price: 79.99, category: "Electronics", brand: "SoundMax", stock_quantity: 50, images: [], attributes: {color: "Black", wireless: "Yes"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Running Shoes", sku: "SPORT-001", description: "Lightweight running shoes", price: 89.99, category: "Sports", brand: "RunFast", stock_quantity: 100, images: [], attributes: {size: "10", color: "Blue"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Cotton T-Shirt", sku: "FASH-001", description: "100% organic cotton", price: 24.99, category: "Fashion", brand: "EcoWear", stock_quantity: 200, images: [], attributes: {size: "M", color: "White"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Coffee Maker", sku: "HOME-001", description: "12-cup programmable coffee maker", price: 49.99, category: "Home", brand: "BrewMaster", stock_quantity: 30, images: [], attributes: {capacity: "12 cups", programmable: "Yes"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Python Programming Book", sku: "BOOK-001", description: "Learn Python from scratch", price: 34.99, category: "Books", brand: "TechBooks", stock_quantity: 75, images: [], attributes: {pages: "450", format: "Paperback"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Smart Watch", sku: "ELEC-002", description: "Fitness tracking smartwatch", price: 149.99, category: "Electronics", brand: "TechTime", stock_quantity: 40, images: [], attributes: {color: "Silver", water_resistant: "Yes"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Yoga Mat", sku: "SPORT-002", description: "Non-slip exercise mat", price: 29.99, category: "Sports", brand: "FlexFit", stock_quantity: 150, images: [], attributes: {thickness: "6mm", color: "Purple"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() },
  { name: "Denim Jacket", sku: "FASH-002", description: "Classic denim jacket", price: 59.99, category: "Fashion", brand: "UrbanStyle", stock_quantity: 80, images: [], attributes: {size: "L", color: "Blue"}, reviews: [], rating: 0, is_active: true, created_at: new Date(), updated_at: new Date() }
])
quit()
```

### Step 6: Test the Application

```bash
# Run unit tests
docker-compose exec product-service pytest -v

# Test health endpoints
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5000/health

# Test product API
curl http://localhost:5001/products

# Test cart API
curl -X POST http://localhost:5002/carts -H "Content-Type: application/json" -d '{"user_id": "test"}'
```

### Step 7: Stop Docker Compose

```bash
docker-compose down

# To remove volumes as well:
docker-compose down -v
```

---

## 8. RUNNING WITH DOCKER COMPOSE

### Commands Reference

```bash
# Start everything
docker-compose up -d

# Start with rebuild
docker-compose up --build -d

# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f frontend

# Scale a service
docker-compose up -d --scale product-service=3

# Restart a service
docker-compose restart cart-service

# Stop everything
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Check status
docker-compose ps
```

---

## 9. KUBERNETES DEPLOYMENT

### Step 1: Start Minikube

```bash
# Start with sufficient resources
minikube start --driver=docker --cpus=4 --memory=6144 --disk-size=20g

# Verify
kubectl cluster-info
kubectl get nodes
```

### Step 2: Point Docker to Minikube (for local images)

```bash
eval $(minikube docker-env)
```

### Step 3: Build Images Inside Minikube

```bash
# Build all 3 service images
docker build -t preet8808/product-service:latest ./product-service
docker build -t preet8808/cart-service:latest ./cart-service
docker build -t preet8808/frontend:latest ./frontend
```

### Step 4: Deploy to Kubernetes

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply configs (order matters!)
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# 3. Deploy database first
kubectl apply -f k8s/mongodb-deployment.yaml
kubectl apply -f k8s/mongodb-service.yaml

# 4. Wait for MongoDB
kubectl wait --namespace=ecomops --for=condition=ready pod --selector=app=mongodb --timeout=180s

# 5. Deploy application services
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/cart-deployment.yaml
kubectl apply -f k8s/cart-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# 6. Deploy monitoring
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/prometheus-service.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/grafana-service.yaml

# 7. Verify everything
kubectl get all -n ecomops
```

### Step 5: Access Services

```bash
# Get Minikube IP
minikube ip

# Open frontend (automatically opens browser)
minikube service frontend -n ecomops

# Get Prometheus URL
minikube service prometheus -n ecomops --url

# Get Grafana URL
minikube service grafana -n ecomops --url

# Port forward for direct access
kubectl port-forward -n ecomops svc/frontend 8080:5000
kubectl port-forward -n ecomops svc/prometheus 9090:9090
kubectl port-forward -n ecomops svc/grafana 3000:3000
```

### Step 6: Seed Data in Kubernetes

```bash
# Port-forward MongoDB
kubectl port-forward -n ecomops svc/mongodb 27017:27017 &

# Insert sample data using mongosh or MongoDB Compass
mongosh mongodb://admin:password123@localhost:27017/ecomops?authSource=admin
# (Use the same insertMany from Step 5 above)
```

---

## 10. MONITORING SETUP

### Accessing Grafana Dashboards

1. Open Grafana: `minikube service grafana -n ecomops`
2. Login: **admin** / **admin123**
3. Navigate to Dashboards > EcomOps > "EcomOps Platform Dashboard"

### Pre-built Dashboard Panels

| Panel | Metric | Alert Threshold |
|-------|--------|----------------|
| Request Rate | `rate(flask_http_request_total[5m])` | Yellow: 100/s, Red: 500/s |
| Response Time (p95) | `histogram_quantile(0.95, ...)` | Baseline monitoring |
| Error Rate (%) | 5xx / total * 100 | Yellow: 1%, Red: 5% |
| Container Health | `up` metric | UP/DOWN status |
| Pod Restarts | `kube_pod_container_status_restarts_total` | Baseline monitoring |

### Prometheus Queries to Try

```promql
# Total requests per service
flask_http_request_total

# 95th percentile response time
histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))

# Error rate
rate(flask_http_request_total{status=~"5.."}[5m])

# Service availability
up{job=~"product-service|cart-service|frontend"}
```

---

## 11. CI/CD PIPELINE CONFIGURATION

### Required GitHub Secrets

| Secret | Value | How to Get |
|--------|-------|------------|
| `DOCKER_USERNAME` | Docker Hub username | Your Docker Hub account |
| `DOCKER_PASSWORD` | Docker Hub access token | Docker Hub > Account Settings > Security |
| `KUBE_CONFIG` | Base64 encoded kubeconfig | `cat ~/.kube/config \| base64 -w 0` |

### Setting Up Secrets

1. Go to GitHub repo > Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add each secret from the table above

### Pipeline Stages

```
Push/PR
  |
  v
Lint (flake8) ----FAIL----> STOP
  | (success)
  v
Test (pytest) ----FAIL----> STOP
  | (success)
  v
Build Docker Images (parallel matrix for 3 services)
  |
  v
Tag: latest + ${{ github.sha }}
  |
  v
Push to Docker Hub
  |
  v
Deploy to Kubernetes (kubectl apply)
  |
  v
Verify Deployments
```

### Manual Pipeline Trigger

```bash
# Make any change and push
echo "# Trigger build" >> README.md
git add README.md
git commit -m "chore: trigger CI/CD pipeline"
git push origin main
```

### Monitor Pipeline

- Go to GitHub repo > Actions tab
- View workflow runs in real-time
- Click on any job to see detailed logs

---

## 12. API REFERENCE

### Product Service API

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|-------------|
| GET | `/health` | Health check | - |
| GET | `/products` | List products (with filters) | Query params |
| POST | `/products` | Create product | `{"name", "price", "sku", "category"}` |
| GET | `/products/<id>` | Get product by ID | - |
| PUT | `/products/<id>` | Update product | `{"name", "price", ...}` |
| DELETE | `/products/<id>` | Soft-delete product | - |
| GET | `/products/category/<cat>` | Filter by category | - |
| POST | `/products/<id>/review` | Add review | `{"rating", "comment", "reviewer"}` |
| GET | `/categories` | List all categories | - |

### Cart Service API

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|-------------|
| GET | `/health` | Health check | - |
| POST | `/carts` | Create cart | `{"user_id"}` |
| GET | `/carts/<id>` | Get cart | - |
| POST | `/carts/<id>/items` | Add item | `{"sku", "name", "price", "quantity"}` |
| PUT | `/carts/<id>/items/<sku>` | Update qty | `{"quantity"}` |
| DELETE | `/carts/<id>/items/<sku>` | Remove item | - |
| POST | `/carts/<id>/apply-coupon` | Apply coupon | `{"code"}` |
| PUT | `/carts/<id>/shipping` | Set shipping | `{"method": "standard/express"}` |
| POST | `/carts/<id>/checkout` | Checkout | `{"payment_method", "shipping_address"}` |
| DELETE | `/carts/<id>` | Delete cart | - |
| GET | `/coupons` | List coupons | - |

### Query Parameters for GET /products

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |
| `category` | string | - | Filter by category |
| `brand` | string | - | Filter by brand |
| `min_price` | float | - | Minimum price |
| `max_price` | float | - | Maximum price |
| `search` | string | - | Full-text search |
| `sort_by` | string | created_at | Sort field |
| `sort_order` | string | desc | asc or desc |

---

## 13. TROUBLESHOOTING

### Common Issues and Solutions

#### Issue: Pods stuck in Pending state
```bash
# Check why
kubectl describe pod -n ecomops <pod-name>

# Common cause: Insufficient resources
minikube delete
minikube start --driver=docker --cpus=4 --memory=8192
```

#### Issue: ImagePullBackOff error
```bash
# Cause: Image not found in registry
# Solution: Build images inside Minikube's Docker
eval $(minikube docker-env)
docker build -t preet8808/product-service:latest ./product-service
# Or use imagePullPolicy: IfNotPresent in deployments
```

#### Issue: MongoDB connection refused
```bash
# Check if MongoDB is running
kubectl get pods -n ecomops -l app=mongodb
kubectl logs -n ecomops <mongodb-pod>

# Verify secrets are applied
kubectl get secrets -n ecomops
kubectl describe secret mongodb-secret -n ecomops
```

#### Issue: Services can't communicate
```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox:1.36 -n ecomops -- nslookup product-service.ecomops.svc.cluster.local

# Check service endpoints
kubectl get endpoints -n ecomops
```

#### Issue: Prometheus not scraping metrics
```bash
# Check targets in Prometheus UI: Status > Targets
# Verify annotation on pods
kubectl get pods -n ecomops -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations}{"\n"}{end}'
```

#### Issue: Grafana dashboards not showing
```bash
# Check datasource
kubectl logs -n ecomops <grafana-pod>

# Verify ConfigMap is mounted
kubectl exec -n ecomops <grafana-pod> -- ls /etc/grafana/provisioning/datasources/
```

#### Issue: CI/CD pipeline failing
```bash
# Check GitHub Actions logs
# Common issues:
# 1. Missing secrets -> Add DOCKER_USERNAME, DOCKER_PASSWORD, KUBE_CONFIG
# 2. Invalid kubeconfig -> Re-generate: cat ~/.kube/config | base64 -w 0
# 3. Docker Hub rate limit -> Use access token instead of password
```

### Debug Commands

```bash
# Get all resources
kubectl get all -n ecomops

# Describe a resource
kubectl describe pod -n ecomops <pod-name>
kubectl describe deployment -n ecomops <deployment-name>
kubectl describe service -n ecomops <service-name>

# View logs
kubectl logs -n ecomops <pod-name>
kubectl logs -n ecomops <pod-name> --previous  # Previous container
kubectl logs -n ecomops -l app=product-service  # All pods with label

# Execute into a pod
kubectl exec -it -n ecomops <pod-name> -- /bin/sh

# Check events
kubectl get events -n ecomops --sort-by=.metadata.creationTimestamp

# Port forward for debugging
kubectl port-forward -n ecomops svc/product-service 5001:5000
```

---

## 14. PRODUCTION CONSIDERATIONS

### Security Enhancements

- [ ] Use TLS/SSL certificates (cert-manager in K8s)
- [ ] Implement proper authentication (OAuth2/JWT)
- [ ] Add NetworkPolicy for pod-to-pod traffic isolation
- [ ] Use HashiCorp Vault or AWS Secrets Manager for secrets
- [ ] Enable PodSecurityPolicy / Pod Security Standards
- [ ] Scan images with Trivy or Snyk
- [ ] Implement rate limiting on APIs

### Scalability Enhancements

- [ ] Replace MongoDB Deployment with StatefulSet + ReplicaSet
- [ ] Add HorizontalPodAutoscaler (HPA) for all services
- [ ] Use Redis for session management and caching
- [ ] Implement API Gateway (Kong, Ambassador, or NGINX Ingress)
- [ ] Add message queue (RabbitMQ/Kafka) for async processing
- [ ] Use CDN for static assets

### Reliability Enhancements

- [ ] Add PersistentVolume with proper storage class
- [ ] Implement backup strategy for MongoDB
- [ ] Add circuit breaker pattern for inter-service calls
- [ ] Configure proper resource quotas and limits
- [ ] Add distributed tracing (Jaeger/Zipkin)
- [ ] Set up alerting with Alertmanager
- [ ] Add liveness/readiness probes to monitoring stack

### Cost Optimization

- [ ] Use Spot instances for non-critical workloads
- [ ] Implement cluster autoscaling
- [ ] Optimize resource requests/limits based on actual usage
- [ ] Use multi-stage builds to minimize image size
- [ ] Consider serverless (Knative) for infrequent workloads

---

## DOCUMENTATION FILES GENERATED

| File | Purpose |
|------|---------|
| `Complete_Project_Guide.md` | This comprehensive guide |
| `GitBash_Command_Reference.md` | 300+ copy-paste commands |
| `k8s/namespace.yaml` | Kubernetes namespace |
| `k8s/secrets.yaml` | MongoDB + app secrets (base64) |
| `k8s/configmap.yaml` | Service configuration |
| `k8s/mongodb-deployment.yaml` | MongoDB + PVC |
| `k8s/mongodb-service.yaml` | MongoDB ClusterIP service |
| `k8s/product-deployment.yaml` | Product service deployment |
| `k8s/product-service.yaml` | Product service ClusterIP |
| `k8s/cart-deployment.yaml` | Cart service deployment |
| `k8s/cart-service.yaml` | Cart service ClusterIP |
| `k8s/frontend-deployment.yaml` | Frontend deployment |
| `k8s/frontend-service.yaml` | Frontend NodePort service |
| `monitoring/prometheus.yml` | Prometheus scrape config |
| `monitoring/prometheus-deployment.yaml` | Prometheus + RBAC |
| `monitoring/prometheus-service.yaml` | Prometheus NodePort |
| `monitoring/grafana-deployment.yaml` | Grafana + dashboards |
| `monitoring/grafana-service.yaml` | Grafana NodePort |
| `.github/workflows/ci-cd.yml` | Full CI/CD pipeline |
| `docker-compose.yml` | Local orchestration |

---

**Project Status:** Complete and Production-Ready
**Last Updated:** 2024-06-11
**Version:** 1.0.0
