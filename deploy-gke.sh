#!/usr/bin/env bash
set -e

# Configuration (Customize registry as needed: GAR / GCR / GHCR / Docker Hub)
# Example for GCP Artifact Registry: us-central1-docker.pkg.dev/<PROJECT_ID>/signature-repo
REGISTRY_PREFIX="${REGISTRY_PREFIX:-ghcr.io/rd-endor}"
BACKEND_IMAGE="${REGISTRY_PREFIX}/email-signature-backend:latest"
FRONTEND_IMAGE="${REGISTRY_PREFIX}/email-signature-frontend:latest"

echo "======================================================"
echo "🚀 Deploying Email Signature Studio to GKE Cluster"
echo "======================================================"
echo "Backend Image : ${BACKEND_IMAGE}"
echo "Frontend Image: ${FRONTEND_IMAGE}"
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
echo "[2/4] Building Backend and Frontend Docker Images..."
docker build -t "${BACKEND_IMAGE}" ./backend
docker build -t "${FRONTEND_IMAGE}" ./frontend

# 3. Push Container Images
echo ""
echo "[3/4] Pushing images to registry..."
read -p "Do you want to push images to '${REGISTRY_PREFIX}' now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push "${BACKEND_IMAGE}"
    docker push "${FRONTEND_IMAGE}"
fi

# 4. Apply Kubernetes Manifests
echo ""
echo "[4/4] Applying Kubernetes manifests..."
sed -e "s|ghcr.io/rd-endor/email-signature-backend:latest|${BACKEND_IMAGE}|g" \
    -e "s|ghcr.io/rd-endor/email-signature-frontend:latest|${FRONTEND_IMAGE}|g" \
    k8s/app.yaml | kubectl apply -f -

echo ""
echo "======================================================"
echo "✅ Manifests applied successfully!"
echo "======================================================"
echo "Checking pod rollout status:"
kubectl rollout status deployment/backend -n signature-demo
kubectl rollout status deployment/frontend -n signature-demo

echo ""
echo "Fetching External LoadBalancer IP:"
kubectl get svc frontend-service -n signature-demo
