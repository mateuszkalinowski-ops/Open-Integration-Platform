#!/usr/bin/env bash
set -euo pipefail

# Creates Kubernetes secrets from CI/CD variables.
# Expected environment variables (set in GitLab CI/CD > Settings > CI/CD > Variables):
#
#   REGISTRY_USERNAME       - Docker registry username
#   REGISTRY_PASSWORD       - Docker registry password
#   DB_ENCRYPTION_KEY       - AES-256 base64-encoded key for credential encryption
#   KAFKA_SASL_USERNAME     - Kafka SASL username (from Strimzi KafkaUser)
#   KAFKA_SASL_PASSWORD     - Kafka SASL password (from Strimzi KafkaUser)
#   ALLEGRO_CLIENT_ID       - Allegro OAuth2 client ID
#   ALLEGRO_CLIENT_SECRET   - Allegro OAuth2 client secret
#   KUBECONFIG_DATA         - base64-encoded kubeconfig for Linode K8s cluster

NAMESPACE="${NAMESPACE:-oip}"

echo "==> Setting up secrets in namespace: $NAMESPACE"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creating registry credentials..."
kubectl create secret docker-registry registry-credentials \
  --namespace "$NAMESPACE" \
  --docker-server=your-registry.example.com \
  --docker-username="${REGISTRY_USERNAME}" \
  --docker-password="${REGISTRY_PASSWORD}" \
  --docker-email=admin@example.com \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creating shared integrator secrets..."
kubectl create secret generic integrator-shared-secrets \
  --namespace "$NAMESPACE" \
  --from-literal=DATABASE_ENCRYPTION_KEY="${DB_ENCRYPTION_KEY}" \
  --from-literal=KAFKA_SASL_USERNAME="${KAFKA_SASL_USERNAME}" \
  --from-literal=KAFKA_SASL_PASSWORD="${KAFKA_SASL_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creating Allegro-specific secrets..."
kubectl create secret generic allegro-integrator-secrets \
  --namespace "$NAMESPACE" \
  --from-literal=DATABASE_ENCRYPTION_KEY="${DB_ENCRYPTION_KEY}" \
  --from-literal=KAFKA_SASL_USERNAME="${KAFKA_SASL_USERNAME}" \
  --from-literal=KAFKA_SASL_PASSWORD="${KAFKA_SASL_PASSWORD}" \
  --from-literal=ALLEGRO_CLIENT_ID="${ALLEGRO_CLIENT_ID:-placeholder}" \
  --from-literal=ALLEGRO_CLIENT_SECRET="${ALLEGRO_CLIENT_SECRET:-placeholder}" \
  --dry-run=client -o yaml | kubectl apply -f -

COURIERS="dhl dpd fedex fedexpl geis gls inpost orlenpaczka packeta paxy pocztapolska schenker sellasist suus ups"

echo "==> Creating courier integrator secrets..."
for courier in $COURIERS; do
  kubectl create secret generic "${courier}-integrator-secrets" \
    --namespace "$NAMESPACE" \
    --from-literal=DATABASE_ENCRYPTION_KEY="${DB_ENCRYPTION_KEY}" \
    --from-literal=KAFKA_SASL_USERNAME="${KAFKA_SASL_USERNAME}" \
    --from-literal=KAFKA_SASL_PASSWORD="${KAFKA_SASL_PASSWORD}" \
    --dry-run=client -o yaml | kubectl apply -f -
done

echo "==> All secrets created successfully."
