#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a fresh Linode Kubernetes cluster for pinquark UAT.
# Run this once on initial cluster setup.
#
# Prerequisites:
#   - kubectl configured with Linode K8s cluster credentials
#   - helm v3 installed
#
# Usage: ./bootstrap-cluster.sh

echo "============================================"
echo "pinquark UAT Cluster Bootstrap"
echo "============================================"

echo ""
echo "==> Step 1: Add Helm repositories..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add strimzi https://strimzi.io/charts/
helm repo update

echo ""
echo "==> Step 2: Install nginx-ingress controller..."
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true \
  --set controller.metrics.serviceMonitor.enabled=true \
  --wait

echo ""
echo "==> Step 3: Install cert-manager..."
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true \
  --version v1.16.0 \
  --wait

echo ""
echo "==> Step 4: Install Strimzi Kafka Operator..."
helm upgrade --install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
  --namespace kafka \
  --create-namespace \
  --set watchNamespaces="{kafka}" \
  --version 0.44.0 \
  --wait

echo ""
echo "==> Step 5: Install kube-prometheus-stack..."
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD:-admin}" \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.label=grafana_dashboard \
  --wait

echo ""
echo "==> Step 6: Apply base infrastructure..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

kubectl apply -k "${PROJECT_ROOT}/k8s/base"

echo ""
echo "==> Step 7: Apply Kafka cluster..."
kubectl apply -k "${PROJECT_ROOT}/k8s/base/kafka"

echo ""
echo "==> Step 8: Apply monitoring resources..."
kubectl apply -k "${PROJECT_ROOT}/k8s/base/monitoring"

echo ""
echo "==> Step 9: Apply ingress and TLS..."
kubectl apply -k "${PROJECT_ROOT}/k8s/base/ingress"

echo ""
echo "==> Step 10: Wait for Kafka to be ready..."
echo "    (this may take 2-5 minutes on first deploy)"
kubectl wait kafka/pinquark-kafka \
  --namespace kafka \
  --for=condition=Ready \
  --timeout=300s || echo "WARNING: Kafka not ready yet. Check: kubectl get kafka -n kafka"

echo ""
echo "============================================"
echo "Cluster bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Point DNS *.uat.pinquark.com to the ingress LoadBalancer IP:"
echo "     kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
echo ""
echo "  2. Create secrets:"
echo "     bash ci/scripts/setup-secrets.sh"
echo ""
echo "  3. Deploy integrators:"
echo "     bash ci/scripts/deploy.sh overlays/uat"
echo "============================================"
