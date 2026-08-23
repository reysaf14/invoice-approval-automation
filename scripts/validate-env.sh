#!/bin/bash
# validate-env.sh — Validate .env file has all required variables
# Usage: bash scripts/validate-env.sh [path-to-env-file]

set -euo pipefail

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found."
    echo "Copy .env.template to .env and fill in your values:"
    echo "  cp .env.template .env"
    exit 1
fi

REQUIRED_VARS=(
    # n8n Core
    "N8N_BASIC_AUTH_USER"
    "N8N_BASIC_AUTH_PASSWORD"
    "N8N_HOST"
    "N8N_PORT"
    "N8N_PROTOCOL"
    "WEBHOOK_URL"
    "GENERIC_TIMEZONE"
    # PostgreSQL
    "DB_TYPE"
    "DB_POSTGRESDB"
    "DB_POSTGRESHOST"
    "DB_POSTGRESPORT"
    "DB_POSTGRESUSER"
    "DB_POSTGRES_PASSWORD"
    # Redis
    "REDIS_HOST"
    "REDIS_PORT"
    # Google
    "GOOGLE_APPLICATION_CREDENTIALS"
    "GOOGLE_SHEETS_SPREADSHEET_ID"
    "GOOGLE_DRIVE_FOLDER_ID"
    # Document AI
    "GOOGLE_DOC_AI_PROJECT_ID"
    "GOOGLE_DOC_AI_LOCATION"
    "GOOGLE_DOC_AI_PROCESSOR_ID"
    # Telegram
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_OWNER_CHAT_ID"
    "TELEGRAM_ADMIN_CHAT_ID"
    # Webhook Security
    "WEBHOOK_HMAC_SECRET"
    "WEBHOOK_TIMESTAMP_TOLERANCE"
)

PLACEHOLDER_PATTERNS=(
    "changeme"
    "your-"
    "xxx"
    "123456789"
    "your-project"
    "your-client-secret"
    "your-gcp-project-id"
    "your-ocr-processor-id"
)

MISSING=0
PLACEHOLDER=0

echo "========================================="
echo " Validating: $ENV_FILE"
echo "========================================="
echo ""

for var in "${REQUIRED_VARS[@]}"; do
    # Check if variable exists and is non-empty
    value=$(grep -E "^${var}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- || true)

    if [ -z "$value" ]; then
        echo "[MISSING] $var"
        MISSING=$((MISSING + 1))
    else
        # Check for placeholder values
        is_placeholder=0
        for pattern in "${PLACEHOLDER_PATTERNS[@]}"; do
            if [[ "$value" == *"$pattern"* ]]; then
                echo "[PLACEHOLDER] $var = $value"
                PLACEHOLDER=$((PLACEHOLDER + 1))
                is_placeholder=1
                break
            fi
        done

        if [ "$is_placeholder" -eq 0 ]; then
            echo "[OK] $var"
        fi
    fi
done

echo ""
echo "========================================="
echo " Summary"
echo "========================================="
echo " Missing:  $MISSING"
echo " Placeholder: $PLACEHOLDER"
echo "========================================="

if [ "$MISSING" -gt 0 ]; then
    echo ""
    echo "ACTION REQUIRED: Fill in missing variables in $ENV_FILE"
    exit 1
fi

if [ "$PLACEHOLDER" -gt 0 ]; then
    echo ""
    echo "WARNING: Some variables still have placeholder values."
    echo "Replace them with real values before starting n8n."
    exit 1
fi

echo ""
echo "All required variables are set. Ready to start!"
exit 0
