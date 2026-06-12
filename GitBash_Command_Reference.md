# EcomOps - Complete Git Bash Command Reference
# Phases 2-4: Kubernetes + Monitoring + CI/CD
# Copy-paste ready commands for Git Bash (Windows) or Terminal (Linux/Mac)
# =============================================================================

# =============================================================================
# SECTION 0: PREREQUISITES & SETUP
# =============================================================================

# --- 0.1 Verify tools are installed ---
kubectl version --client
minikube version
# OR
docker --version

# --- 0.2 Clone the repository ---
git clone https://github.com/Preet8808/EcomOps.git
cd EcomOps

# --- 0.3 Set your Docker Hub username (run this first) ---
export DOCKER_USERNAME="preet8808"
# On Windows Git Bash: set DOCKER_USERNAME=preet8808

# =============================================================================
# SECTION 1: FOLDER & FILE CREATION COMMANDS
# =============================================================================

# --- 1.1 Create all required directories ---
mkdir -p k8s
mkdir -p monitoring
mkdir -p .github/workflows
mkdir -p product-service
mkdir -p cart-service
mkdir -p frontend
mkdir -p tests

# --- 1.2 Verify directory structure ---
tree -L 2
# OR
find . -maxdepth 2 -type d | sort

# --- 1.3 Create empty files (if starting fresh) ---
touch k8s/namespace.yaml
touch k8s/configmap.yaml
touch k8s/secrets.yaml
touch k8s/mongodb-deployment.yaml
touch k8s/mongodb-service.yaml
touch k8s/product-deployment.yaml
touch k8s/product-service.yaml
touch k8s/cart-deployment.yaml
touch k8s/cart-service.yaml
touch k8s/frontend-deployment.yaml
touch k8s/frontend-service.yaml
touch monitoring/prometheus.yml
touch monitoring/prometheus-deployment.yaml
touch monitoring/prometheus-service.yaml
touch monitoring/grafana-deployment.yaml
touch monitoring/grafana-service.yaml
touch .github/workflows/ci-cd.yml

# =============================================================================
# SECTION 2: START MINIKUBEr
# =============================================================================

# --- 2.1 Start Minikube with sufficient resources ---
minikube start --driver=docker --cpus=4 --memory=6144 --disk-size=20g

# --- 2.2 Verify cluster is running ---
kubectl cluster-info
kubectl get nodes

# --- 2.3 Enable required addons ---
minikube addons enable metrics-server
minikube addons enable dashboard

# --- 2.4 Point Docker to Minikube's Docker daemon (for local builds) ---
# IMPORTANT: Run this in the same terminal where you'll build images
eval $(minikube docker-env)
# On Windows Git Bash: eval $(minikube docker-env)

# =============================================================================
# SECTION 3: CREATE & APPLY KUBERNETES MANIFESTS (PHASE 2)
# =============================================================================

# --- 3.0 Create namespace first ---
kubectl apply -f k8s/namespace.yaml

# --- 3.1 Verify namespace was created ---
kubectl get namespaces
echo "ecomops namespace should appear in the list"

# --- 3.2 Apply ConfigMap and Secrets (order matters: before deployments) ---
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# --- 3.3 Verify secrets and configmap ---
kubectl get secrets -n ecomops
kubectl get configmap -n ecomops
kubectl describe secret mongodb-secret -n ecomops
kubectl describe configmap ecomops-config -n ecomops

# --- 3.4 Apply MongoDB (database first) ---
kubectl apply -f k8s/mongodb-deployment.yaml
kubectl apply -f k8s/mongodb-service.yaml

# --- 3.5 Wait for MongoDB to be ready ---
kubectl wait --namespace=ecomops \
  --for=condition=ready pod \
  --selector=app=mongodb \
  --timeout=180s

# --- 3.6 Apply application services ---
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/cart-deployment.yaml
kubectl apply -f k8s/cart-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# --- 3.7 Wait for all backend services to be ready ---
kubectl wait --namespace=ecomops \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=backend \
  --timeout=180s

# --- 3.8 Apply all at once (shortcut for experienced users) ---
# kubectl apply -f k8s/

# =============================================================================
# SECTION 4: VERIFY DEPLOYMENTS & PODS
# =============================================================================

# --- 4.1 List all resources in the ecomops namespace ---
kubectl get all -n ecomops

# --- 4.2 List pods with wide output (shows IP, node) ---
kubectl get pods -n ecomops -o wide

# --- 4.3 Check pod status in detail ---
kubectl get pods -n ecomops --show-labels

# --- 4.4 Describe a specific pod (troubleshooting) ---
# Replace <pod-name> with actual pod name from kubectl get pods
kubectl describe pod -n ecomops <pod-name>

# --- 4.5 View pod logs ---
kubectl logs -n ecomops <pod-name>

# --- 4.6 Follow pod logs in real-time ---
kubectl logs -n ecomops <pod-name> -f

# --- 4.7 View logs for all pods of a deployment ---
kubectl logs -n ecomops -l app=product-service --tail=50
kubectl logs -n ecomops -l app=cart-service --tail=50
kubectl logs -n ecomops -l app=frontend --tail=50
kubectl logs -n ecomops -l app=mongodb --tail=50

# --- 4.8 Check deployment status ---
kubectl get deployments -n ecomops
kubectl rollout status deployment/product-service -n ecomops
kubectl rollout status deployment/cart-service -n ecomops
kubectl rollout status deployment/frontend -n ecomops
kubectl rollout status deployment/mongodb -n ecomops

# --- 4.9 View replica sets ---
kubectl get rs -n ecomops

# --- 4.10 View events (sorted by time) ---
kubectl get events -n ecomops --sort-by=.metadata.creationTimestamp

# =============================================================================
# SECTION 5: VERIFY SERVICES & NETWORKING
# =============================================================================

# --- 5.1 List all services ---
kubectl get svc -n ecomops

# --- 5.2 Describe a specific service ---
kubectl describe svc product-service -n ecomops
kubectl describe svc cart-service -n ecomops
kubectl describe svc frontend -n ecomops
kubectl describe svc mongodb -n ecomops

# --- 5.3 Get service endpoints ---
kubectl get endpoints -n ecomops

# --- 5.4 Test internal DNS resolution ---
# Run a temporary pod to test DNS
kubectl run -it --rm debug --image=busybox:1.36 --restart=Never -n ecomops -- nslookup mongodb.ecomops.svc.cluster.local
kubectl run -it --rm debug --image=busybox:1.36 --restart=Never -n ecomops -- nslookup product-service.ecomops.svc.cluster.local
kubectl run -it --rm debug --image=busybox:1.36 --restart=Never -n ecomops -- nslookup cart-service.ecomops.svc.cluster.local

# --- 5.5 Test service connectivity with curl ---
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n ecomops -- curl -s http://product-service.ecomops.svc.cluster.local:5000/health
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n ecomops -- curl -s http://cart-service.ecomops.svc.cluster.local:5000/health
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n ecomops -- curl -s http://frontend.ecomops.svc.cluster.local:5000/health

# =============================================================================
# SECTION 6: ACCESS THE FRONTEND APPLICATION
# =============================================================================

# --- 6.1 Get the Minikube IP ---
minikube ip

# --- 6.2 Get the NodePort for frontend ---
kubectl get svc frontend -n ecomops

# --- 6.3 Open the frontend in browser (Minikube) ---
minikube service frontend -n ecomops --url

# --- 6.4 Open frontend directly in browser ---
minikube service frontend -n ecomops

# --- 6.5 Alternative: Port-forward frontend to localhost ---
kubectl port-forward -n ecomops svc/frontend 8080:5000
# Then open: http://localhost:8080
# Press Ctrl+C to stop

# =============================================================================
# SECTION 7: DEPLOY MONITORING STACK (PHASE 3)
# =============================================================================

# --- 7.1 Apply Prometheus resources ---
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/prometheus-service.yaml

# --- 7.2 Wait for Prometheus to be ready ---
kubectl wait --namespace=ecomops \
  --for=condition=ready pod \
  --selector=app=prometheus \
  --timeout=180s

# --- 7.3 Apply Grafana resources ---
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/grafana-service.yaml

# --- 7.4 Wait for Grafana to be ready ---
kubectl wait --namespace=ecomops \
  --for=condition=ready pod \
  --selector=app=grafana \
  --timeout=180s

# --- 7.5 Apply all monitoring at once ---
# kubectl apply -f monitoring/

# --- 7.6 Verify monitoring pods ---
kubectl get pods -n ecomops -l app.kubernetes.io/component=monitoring

# =============================================================================
# SECTION 8: PORT FORWARD PROMETHEUS & GRAFANA
# =============================================================================

# --- 8.1 Port-forward Prometheus to localhost:9090 ---
# Open a NEW terminal and run:
kubectl port-forward -n ecomops svc/prometheus 9090:9090
# Then open: http://localhost:9090
# Press Ctrl+C to stop

# --- 8.2 Port-forward Grafana to localhost:3000 ---
# Open ANOTHER new terminal and run:
kubectl port-forward -n ecomops svc/grafana 3000:3000
# Then open: http://localhost:3000
# Press Ctrl+C to stop

# --- 8.3 Alternative: Use Minikube service URLs ---
minikube service prometheus -n ecomops --url
minikube service grafana -n ecomops --url

# --- 8.4 Grafana login credentials ---
# Username: admin
# Password: admin123

# =============================================================================
# SECTION 9: VERIFY METRICS COLLECTION
# =============================================================================

# --- 9.1 Check if Prometheus targets are UP ---
# In Prometheus UI (localhost:9090), go to Status > Targets
# All targets should show State = UP

# --- 9.2 Query request count in Prometheus ---
# In Prometheus query box, enter:
# flask_http_request_total

# --- 9.3 Query response time in Prometheus ---
# histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))

# --- 9.4 Query error rate in Prometheus ---
# rate(flask_http_request_total{status=~"5.."}[5m])

# --- 9.5 Query container health ---
# up{job=~"product-service|cart-service|frontend"}

# --- 9.6 Test metrics endpoint directly ---
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n ecomops -- curl -s http://product-service.ecomops.svc.cluster.local:5000/metrics | head -20

# =============================================================================
# SECTION 10: CI/CD SETUP (PHASE 4)
# =============================================================================

# --- 10.1 Add GitHub Actions workflow to repository ---
git add .github/workflows/ci-cd.yml
git commit -m "feat(ci/cd): add complete CI/CD pipeline with lint, test, build, push, deploy"
git push origin main

# --- 10.2 Set up GitHub Secrets (via GitHub UI or CLI) ---
# Required secrets:
#   DOCKER_USERNAME    - Your Docker Hub username
#   DOCKER_PASSWORD    - Your Docker Hub password or access token
#   KUBE_CONFIG        - Base64 encoded kubeconfig file

# --- 10.3 Generate base64 kubeconfig for GitHub Secret ---
cat ~/.kube/config | base64 -w 0
# On Mac: cat ~/.kube/config | base64
# Copy the output and paste into GitHub Secret as KUBE_CONFIG

# --- 10.4 Trigger pipeline manually (by making a change) ---
echo "# Trigger build" >> README.md
git add README.md
git commit -m "chore: trigger CI pipeline"
git push origin main

# --- 10.5 View GitHub Actions workflow status ---
# Go to: https://github.com/Preet8808/EcomOps/actions

# =============================================================================
# SECTION 11: SCALING OPERATIONS
# =============================================================================

# --- 11.1 Scale a deployment manually ---
kubectl scale deployment product-service --replicas=3 -n ecomops
kubectl scale deployment cart-service --replicas=3 -n ecomops
kubectl scale deployment frontend --replicas=3 -n ecomops

# --- 11.2 Verify scaling ---
kubectl get pods -n ecomops

# --- 11.3 Scale back down ---
kubectl scale deployment product-service --replicas=2 -n ecomops
kubectl scale deployment cart-service --replicas=2 -n ecomops
kubectl scale deployment frontend --replicas=2 -n ecomops

# =============================================================================
# SECTION 12: ROLLING UPDATES & ROLLBACKS
# =============================================================================

# --- 12.1 Update an image (rolling update) ---
kubectl set image deployment/product-service product-service=preet8808/product-service:v2.0 -n ecomops

# --- 12.2 Watch the rollout ---
kubectl rollout status deployment/product-service -n ecomops

# --- 12.3 View rollout history ---
kubectl rollout history deployment/product-service -n ecomops

# --- 12.4 Rollback to previous version ---
kubectl rollout undo deployment/product-service -n ecomops

# --- 12.5 Rollback to specific revision ---
kubectl rollout undo deployment/product-service --to-revision=1 -n ecomops

# =============================================================================
# SECTION 13: TROUBLESHOOTING COMMANDS
# =============================================================================

# --- 13.1 Check why a pod is failing ---
kubectl describe pod -n ecomops <pod-name>

# --- 13.2 View previous container logs (if pod restarted) ---
kubectl logs -n ecomops <pod-name> --previous

# --- 13.3 Execute into a running container ---
kubectl exec -it -n ecomops <pod-name> -- /bin/sh
# For MongoDB: kubectl exec -it -n ecomops <mongodb-pod> -- mongosh -u admin -p password123 --authenticationDatabase admin

# --- 13.4 Check resource usage ---
kubectl top pod -n ecomops
kubectl top node

# --- 13.5 Check for image pull errors ---
kubectl get events -n ecomops | grep -i "failed\|pull\|error"

# --- 13.6 Restart a deployment ---
kubectl rollout restart deployment/product-service -n ecomops
kubectl rollout restart deployment/cart-service -n ecomops
kubectl rollout restart deployment/frontend -n ecomops

# --- 13.7 Delete and recreate everything ---
kubectl delete -f k8s/ -n ecomops
kubectl delete -f monitoring/ -n ecomops
kubectl apply -f k8s/
kubectl apply -f monitoring/

# --- 13.8 Check PVC status ---
kubectl get pvc -n ecomops
kubectl describe pvc mongodb-pvc -n ecomops

# =============================================================================
# SECTION 14: CLEANUP COMMANDS
# =============================================================================

# --- 14.1 Delete specific resources ---
kubectl delete -f k8s/frontend-deployment.yaml -n ecomops
kubectl delete -f k8s/frontend-service.yaml -n ecomops

# --- 14.2 Delete all application resources ---
kubectl delete -f k8s/ -n ecomops

# --- 14.3 Delete monitoring resources ---
kubectl delete -f monitoring/ -n ecomops

# --- 14.4 Delete the entire namespace (nuclear option) ---
kubectl delete namespace ecomops

# --- 14.5 Delete Minikube cluster ---
minikube delete

# =============================================================================
# SECTION 15: COMPLETE DEPLOYMENT SUMMARY (ONE-SHOT)
# =============================================================================

# --- 15.1 Full deployment from scratch ---
# Step 1: Start Minikube
minikube start --driver=docker --cpus=4 --memory=6144

# Step 2: Create namespace
cd EcomOps
kubectl apply -f k8s/namespace.yaml

# Step 3: Apply configs (secrets + configmap)
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Step 4: Deploy MongoDB
kubectl apply -f k8s/mongodb-deployment.yaml
kubectl apply -f k8s/mongodb-service.yaml
kubectl wait --namespace=ecomops --for=condition=ready pod --selector=app=mongodb --timeout=180s

# Step 5: Deploy application services
kubectl apply -f k8s/product-deployment.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/cart-deployment.yaml
kubectl apply -f k8s/cart-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

# Step 6: Deploy monitoring
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/prometheus-service.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/grafana-service.yaml

# Step 7: Verify everything
kubectl get all -n ecomops

# Step 8: Open services
minikube service frontend -n ecomops --url

# =============================================================================
# QUICK REFERENCE: Common kubectl Commands
# =============================================================================
# kubectl get pods -n ecomops                    # List pods
# kubectl get svc -n ecomops                     # List services
# kubectl get deployments -n ecomops             # List deployments
# kubectl get events -n ecomops                  # List events
# kubectl logs <pod> -n ecomops                  # View logs
# kubectl describe <resource> <name> -n ecomops  # Describe resource
# kubectl exec -it <pod> -n ecomops -- /bin/sh  # Shell into pod
# kubectl port-forward svc/<name> <local>:<remote> -n ecomops  # Port forward
# kubectl apply -f <file.yaml>                   # Apply manifest
# kubectl delete -f <file.yaml>                  # Delete manifest
# kubectl rollout status deployment/<name> -n ecomops  # Check rollout
# kubectl rollout undo deployment/<name> -n ecomops    # Rollback
# kubectl top pod -n ecomops                     # Resource usage
# =============================================================================
