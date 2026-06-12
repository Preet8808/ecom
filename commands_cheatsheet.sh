#!/usr/bin/env bash

# =============================================================================
# EcomOps - DevOps Project Commands Cheat Sheet
# For Local Docker Compose and Kubernetes (Minikube) Deployments
# =============================================================================

echo "================================================================"
echo "           EcomOps DevOps Commands Reference Sheet               "
echo "================================================================"
echo "To run any section, copy the commands below and paste into Git Bash."
echo ""

# -----------------------------------------------------------------------------
# 🐳 SECTION 1: DOCKER COMPOSE COMMANDS (Local Development & Testing)
# -----------------------------------------------------------------------------

# 1. Start all containers in the background (builds images if code changed)
# docker-compose up --build -d

# 2. Check the status and health of all running containers
# docker-compose ps

# 3. Stream all logs in real-time
# docker-compose logs -f

# 4. View logs for a specific service (e.g. frontend)
# docker-compose logs -f frontend

# 5. Restart a single service container (e.g. after code modification)
# docker-compose restart product-service

# 6. Stop all containers, keeping database volumes intact
# docker-compose down

# 7. Stop all containers and wipe all database volumes (clean state reset)
# docker-compose down -v


# -----------------------------------------------------------------------------
# ☸️ SECTION 2: KUBERNETES DEPLOYMENT COMMANDS (Minikube Cluster)
# -----------------------------------------------------------------------------

# Step 1: Start the Minikube local cluster with resource allocations
# minikube start --driver=docker --cpus=4 --memory=6144

# Step 2: Configure shell context to build Docker images inside Minikube
# eval $(minikube docker-env)

# Step 3: Build application images inside Minikube's Docker daemon
# docker build -t preet8808/product-service:latest ./product-service
# docker build -t preet8808/cart-service:latest ./cart-service
# docker build -t preet8808/frontend:latest ./frontend

# Step 4: Apply K8s Configuration & Secrets (Order of application matters)
# kubectl apply -f k8s/namespace.yaml
# kubectl apply -f k8s/secrets.yaml
# kubectl apply -f k8s/configmap.yaml

# Step 5: Deploy MongoDB first and wait for it to be fully ready
# kubectl apply -f k8s/mongodb-deployment.yaml
# kubectl apply -f k8s/mongodb-service.yaml
# kubectl wait --namespace=ecomops --for=condition=ready pod --selector=app=mongodb --timeout=120s

# Step 6: Deploy Microservices
# kubectl apply -f k8s/product-deployment.yaml
# kubectl apply -f k8s/product-service.yaml
# kubectl apply -f k8s/cart-deployment.yaml
# kubectl apply -f k8s/cart-service.yaml
# kubectl apply -f k8s/frontend-deployment.yaml
# kubectl apply -f k8s/frontend-service.yaml

# Step 7: Deploy Monitoring Stack (Prometheus & Grafana)
# kubectl apply -f monitoring/prometheus-deployment.yaml
# kubectl apply -f monitoring/prometheus-service.yaml
# kubectl apply -f monitoring/grafana-deployment.yaml
# kubectl apply -f monitoring/grafana-service.yaml

# Step 8: Verify cluster resources
# kubectl get all -n ecomops

# Step 9: Launch browser service endpoints
# minikube service frontend -n ecomops
# minikube service grafana -n ecomops


# -----------------------------------------------------------------------------
# 🧪 SECTION 3: QUICK TEST TRAFFIC COMMANDS (Run to generate graph spikes)
# -----------------------------------------------------------------------------

# Run these in a loop to generate request metrics for Grafana charts:
# for i in {1..20}; do
#   curl -I http://localhost:5000/
#   curl -I http://localhost:5000/products
#   curl -I http://localhost:5000/invalid-page-test
#   sleep 0.2
# done
