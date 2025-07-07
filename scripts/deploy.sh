#!/bin/bash

# Kubernetes Deployment Script for Capstone Backend
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
NAMESPACE=${2:-default}

echo "🚀 Deploying Capstone Backend to Kubernetes..."
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations in order
echo "📝 Applying ConfigMap..."
kubectl apply -f k8s/configmap.yaml -n $NAMESPACE

echo "🔐 Applying Secrets..."
kubectl apply -f k8s/secrets.yaml -n $NAMESPACE

echo "💾 Applying PersistentVolumeClaim..."
kubectl apply -f k8s/deployment.yaml -n $NAMESPACE

echo "🔄 Waiting for deployment to be ready..."
kubectl rollout status deployment/capstone-backend-deployment -n $NAMESPACE --timeout=300s

echo "🌐 Applying Service..."
kubectl apply -f k8s/ingress.yaml -n $NAMESPACE

echo "✅ Deployment completed successfully!"
echo "🔍 Checking deployment status..."
kubectl get pods -n $NAMESPACE -l app=capstone-backend
kubectl get svc -n $NAMESPACE capstone-backend-service

echo "📊 Deployment information:"
kubectl describe deployment capstone-backend-deployment -n $NAMESPACE
