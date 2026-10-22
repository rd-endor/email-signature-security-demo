#!/usr/bin/env bash
set -e

# Configuration (Customize registry as needed: GAR / GCR / GHCR / Docker Hub)
# Default: GCP Artifact Registry in endor-experiments
REGISTRY_PREFIX="${REGISTRY_PREFIX:-us-central1-docker.pkg.dev/endor-experiments/demo-repository}"
BACKEND_IMAGE="${REGISTRY_PREFIX}/email-signature-backend:latest"
FRONTEND_IMAGE="${REGISTRY_PREFIX}/email-signature-frontend:latest"
PHP_IMAGE="${REGISTRY_PREFIX}/email-signature-php:latest"

# Internet exposure flag: true = public LoadBalancer, false (default) = private ClusterIP
INTERNET_EXPOSURE="${INTERNET_EXPOSURE:-false}"
if [[ "${INTERNET_EXPOSURE}" == "true" ]]; then
    FRONTEND_SERVICE_TYPE="LoadBalancer"
else
    FRONTEND_SERVICE_TYPE="ClusterIP"
fi

echo "======================================================"
echo "🚀 Deploying Email Signature Studio to GKE Cluster"
echo "======================================================"
echo "Backend Image     : ${BACKEND_IMAGE}"
echo "Frontend Image    : ${FRONTEND_IMAGE}"
echo "PHP Image         : ${PHP_IMAGE}"
echo "Internet Exposure : ${INTERNET_EXPOSURE} (Service Type: ${FRONTEND_SERVICE_TYPE})"
echo ""

# 1. Check kubectl connection
echo "[1/4] Verifying kubectl connection to cluster..."
kubectl cluster-info || {
    echo "❌ Error: kubectl is not connected to a Kubernetes cluster."
    echo "Run: gcloud container clusters get-credentials <CLUSTER_NAME> --region=<REGION>"
    exit 1
}

# 2. Build Container Images
echo ""
echo "[2/4] Building Backend, Frontend, and PHP Docker Images (linux/amd64 for GKE)..."
docker build --platform linux/amd64 -t "${BACKEND_IMAGE}" ./backend
docker build --platform linux/amd64 -t "${FRONTEND_IMAGE}" ./frontend
docker build --platform linux/amd64 -t "${PHP_IMAGE}" ./php

# 3. Push Container Images
echo ""
echo "[3/4] Pushing images to registry..."
read -p "Do you want to push images to '${REGISTRY_PREFIX}' now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push "${BACKEND_IMAGE}"
    docker push "${FRONTEND_IMAGE}"
    docker push "${PHP_IMAGE}"
fi

# 4. Apply Kubernetes Manifests
echo ""
echo "[4/4] Applying Kubernetes manifests..."
sed -e "s|ghcr.io/rd-endor/email-signature-backend:latest|${BACKEND_IMAGE}|g" \
    -e "s|ghcr.io/rd-endor/email-signature-frontend:latest|${FRONTEND_IMAGE}|g" \
    -e "s|ghcr.io/rd-endor/email-signature-php:latest|${PHP_IMAGE}|g" \
    -e "s|type: ClusterIP # FRONTEND_SERVICE_TYPE|type: ${FRONTEND_SERVICE_TYPE}|g" \
    k8s/app.yaml | kubectl apply -f -

echo ""
echo "======================================================"
echo "✅ Manifests applied successfully!"
echo "======================================================"
echo "Checking pod rollout status:"
kubectl rollout status deployment/backend -n signature-demo
kubectl rollout status deployment/frontend -n signature-demo
kubectl rollout status deployment/php -n signature-demo

echo ""
echo "Frontend Service Status:"
kubectl get svc frontend-service -n signature-demo

if [[ "${INTERNET_EXPOSURE}" == "false" ]]; then
    echo ""
    echo "🔒 Internet exposure is DISABLED (ClusterIP)."
    echo "To access the application locally on your machine, run:"
    echo "   kubectl port-forward svc/frontend-service 8080:80 -n signature-demo"
    echo "Then open: http://localhost:8080"
fi
