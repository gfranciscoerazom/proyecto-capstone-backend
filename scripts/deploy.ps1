# Kubernetes Deployment Script for Capstone Backend (PowerShell)
# Usage: .\deploy.ps1 [-Environment "production"] [-Namespace "default"]

param(
    [string]$Environment = "production",
    [string]$Namespace = "default"
)

Write-Host "🚀 Deploying Capstone Backend to Kubernetes..." -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Namespace: $Namespace" -ForegroundColor Yellow

# Check if kubectl is installed
try {
    kubectl version --client --short | Out-Null
} catch {
    Write-Host "❌ kubectl is not installed. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# Check if we can connect to the cluster
try {
    kubectl cluster-info | Out-Null
} catch {
    Write-Host "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig." -ForegroundColor Red
    exit 1
}

# Create namespace if it doesn't exist
Write-Host "📁 Creating namespace if it doesn't exist..." -ForegroundColor Blue
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations in order
Write-Host "📝 Applying ConfigMap..." -ForegroundColor Blue
kubectl apply -f k8s/configmap.yaml -n $Namespace

Write-Host "🔐 Applying Secrets..." -ForegroundColor Blue
kubectl apply -f k8s/secrets.yaml -n $Namespace

Write-Host "🚀 Applying Deployment..." -ForegroundColor Blue
kubectl apply -f k8s/deployment.yaml -n $Namespace

Write-Host "🔄 Waiting for deployment to be ready..." -ForegroundColor Blue
kubectl rollout status deployment/capstone-backend-deployment -n $Namespace --timeout=300s

Write-Host "🌐 Applying Ingress..." -ForegroundColor Blue
kubectl apply -f k8s/ingress.yaml -n $Namespace

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "🔍 Checking deployment status..." -ForegroundColor Blue

kubectl get pods -n $Namespace -l app=capstone-backend
kubectl get svc -n $Namespace capstone-backend-service

Write-Host "📊 Deployment information:" -ForegroundColor Blue
kubectl describe deployment capstone-backend-deployment -n $Namespace
