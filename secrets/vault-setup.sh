#!/bin/bash
#
# AgentFlow Secrets Setup Script
# Supports HashiCorp Vault and AWS Secrets Manager
# Usage: ./secrets/vault-setup.sh [vault|aws] <environment>
#

set -e

ENVIRONMENT="${2:-dev}"
SECRET_PROVIDER="${1:-vault}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate random secrets
generate_secret() {
    head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 32
}

setup_vault() {
    log_info "Setting up secrets in HashiCorp Vault for $ENVIRONMENT..."

    VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
    VAULT_TOKEN="${VAULT_TOKEN:-}"

    if [ -z "$VAULT_TOKEN" ]; then
        log_error "VAULT_TOKEN environment variable not set"
        exit 1
    fi

    # Define secret paths
    SECRET_PATH="secret/agentflow/$ENVIRONMENT"

    # Generate secrets
    DB_URL="postgresql://agentflow:$(generate_secret)@postgres:5432/agentflow"
    JWT_SECRET=$(generate_secret)
    API_KEY=$(generate_secret)
    WEAVIATE_KEY=$(generate_secret)
    REDIS_PASSWORD=$(generate_secret)

    # Write secrets to Vault
    log_info "Writing database credentials..."
    vault kv put "$SECRET_PATH/database \
        url="$DB_URL" \
        username="agentflow" \
        password="$(generate_secret)"

    log_info "Writing JWT secret..."
    vault kv put "$SECRET_PATH/jwt" secret="$JWT_SECRET"

    log_info "Writing API key..."
    vault kv put "$SECRET_PATH/api" key="$API_KEY"

    log_info "Writing Weaviate API key..."
    vault kv put "$SECRET_PATH/weaviate" apiKey="$WEAVIATE_KEY"

    log_info "Writing Redis password..."
    vault kv put "$SECRET_PATH/redis" password="$REDIS_PASSWORD"

    log_info "Creating Kubernetes auth role for AgentFlow..."
    vault policy write agentflow-publisher - <<'EOF'
path "secret/agentflow/*" {
  capabilities = ["read"]
}
EOF

    log_info "Vault secrets setup complete!"
    log_info "Secret path: $SECRET_PATH"
}

setup_aws_secrets() {
    log_info "Setting up secrets in AWS Secrets Manager for $ENVIRONMENT..."

    REGION="${AWS_REGION:-us-east-1}"
    SECRET_PREFIX="agentflow/$ENVIRONMENT"

    # Check if AWS CLI is configured
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi

    # Generate secrets
    DB_URL="postgresql://agentflow:$(generate_secret)@postgres:5432/agentflow"
    JWT_SECRET=$(generate_secret)
    API_KEY=$(generate_secret)
    WEAVIATE_KEY=$(generate_secret)
    REDIS_PASSWORD=$(generate_secret)

    # Create secrets
    log_info "Creating database credentials secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_PREFIX/database" \
        --secret-string "{\"url\":\"$DB_URL\",\"username\":\"agentflow\",\"password\":\"$(generate_secret)\"}" \
        --region "$REGION"

    log_info "Creating JWT secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_PREFIX/jwt" \
        --secret-string "{\"secret\":\"$JWT_SECRET\"}" \
        --region "$REGION"

    log_info "Creating API key secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_PREFIX/api" \
        --secret-string "{\"key\":\"$API_KEY\"}" \
        --region "$REGION"

    log_info "Creating Weaviate API key secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_PREFIX/weaviate" \
        --secret-string "{\"apiKey\":\"$WEAVIATE_KEY\"}" \
        --region "$REGION"

    log_info "Creating Redis password secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_PREFIX/redis" \
        --secret-string "{\"password\":\"$REDIS_PASSWORD\"}" \
        --region "$REGION"

    # Create IAM policy for Kubernetes service account
    log_info "Creating IAM policy for AgentFlow..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "AgentFlow-$ENVIRONMENT" \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": [
                        "arn:aws:secretsmanager:'$REGION':*:secret:agentflow/'"$ENVIRONMENT"'/*"
                    ]
                }
            ]
        }' \
        --query 'Policy.Arn' \
        --output text)

    log_info "Policy ARN: $POLICY_ARN"
    log_info "AWS Secrets Manager setup complete!"
    log_info "Secret prefix: $SECRET_PREFIX"
}

# Kubernetes Secret sync (for external secrets operators)
setup_kubernetes_external_secrets() {
    log_info "Setting up External Secrets Operator configuration..."

    cat <<'EOF'
# Apply this ExternalSecret configuration to sync secrets from Vault or AWS

apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agentflow-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: agentflow-secrets
    creationPolicy: Owner
  data:
    - secretKey: database-url
      remoteRef:
        key: secret/agentflow/dev/database
        property: url
    - secretKey: jwt-secret
      remoteRef:
        key: secret/agentflow/dev/jwt
        property: secret
    - secretKey: api-key
      remoteRef:
        key: secret/agentflow/dev/api
        property: key
EOF
}

show_usage() {
    echo "Usage: $0 [provider] [environment]"
    echo ""
    echo "Providers:"
    echo "  vault   - HashiCorp Vault (default)"
    echo "  aws     - AWS Secrets Manager"
    echo "  k8s     - Generate External Secrets Operator config"
    echo ""
    echo "Environment: dev, staging, prod (default: dev)"
    echo ""
    echo "Environment variables:"
    echo "  VAULT_ADDR      - Vault server address (for vault provider)"
    echo "  VAULT_TOKEN     - Vault token (for vault provider)"
    echo "  AWS_REGION      - AWS region (for aws provider)"
    echo ""
    echo "Examples:"
    echo "  $0 vault prod          # Setup Vault secrets for production"
    echo "  $0 aws staging         # Setup AWS secrets for staging"
    echo "  $0 k8s                 # Generate External Secrets config"
}

case "$SECRET_PROVIDER" in
    vault)
        setup_vault
        ;;
    aws)
        setup_aws_secrets
        ;;
    k8s)
        setup_kubernetes_external_secrets
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown provider: $SECRET_PROVIDER"
        show_usage
        exit 1
        ;;
esac

log_info "Done!"