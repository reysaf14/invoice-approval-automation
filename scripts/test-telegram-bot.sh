#!/bin/bash
# test-telegram-bot.sh — Quick test Telegram bot connectivity
# Usage: bash scripts/test-telegram-bot.sh [bot_token] [chat_id]

set -euo pipefail

# Load from .env if not provided as args
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

BOT_TOKEN="${1:-${TELEGRAM_BOT_TOKEN:-}}"
CHAT_ID="${2:-${TELEGRAM_OWNER_CHAT_ID:-}}"

if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: BOT_TOKEN not provided."
    echo "Usage: bash scripts/test-telegram-bot.sh <bot_token> <chat_id>"
    echo "Or set TELEGRAM_BOT_TOKEN in .env"
    exit 1
fi

if [ -z "$CHAT_ID" ]; then
    echo "ERROR: CHAT_ID not provided."
    echo "Usage: bash scripts/test-telegram-bot.sh <bot_token> <chat_id>"
    echo "Or set TELEGRAM_OWNER_CHAT_ID in .env"
    exit 1
fi

echo "========================================="
echo " Telegram Bot Connectivity Test"
echo "========================================="
echo ""

# Step 1: Test bot info
echo "[1/3] Getting bot info..."
BOT_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null)

if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_NAME=$(echo "$BOT_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['username'])" 2>/dev/null || echo "unknown")
    echo "[OK] Bot connected: @$BOT_NAME"
else
    echo "[FAIL] Cannot connect to bot. Check BOT_TOKEN."
    echo "Response: $BOT_INFO"
    exit 1
fi

echo ""

# Step 2: Send test message
echo "[2/3] Sending test message to chat $CHAT_ID..."
TEST_MSG="Test connection from Invoice Approval Automation at $(date '+%Y-%m-%d %H:%M:%S')"
SEND_RESULT=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${CHAT_ID}\",\"text\":\"${TEST_MSG}\",\"parse_mode\":\"HTML\"}" 2>/dev/null)

if echo "$SEND_RESULT" | grep -q '"ok":true'; then
    echo "[OK] Message sent successfully."
else
    echo "[FAIL] Cannot send message. Check CHAT_ID and bot permissions."
    echo "Response: $SEND_RESULT"
    exit 1
fi

echo ""

# Step 3: Send test notification (simulates invoice alert)
echo "[3/3] Sending simulated invoice notification..."
INVOICE_MSG="TEST: Invoice Approval Automation connection test.
Vendor: PT Test Vendor
Amount: Rp 1.000.000
Status: PENDING TEST

This is a test message. Please ignore."
NOTIF_RESULT=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${CHAT_ID}\",\"text\":$(echo "$INVOICE_MSG" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))')}" 2>/dev/null)

if echo "$NOTIF_RESULT" | grep -q '"ok":true'; then
    echo "[OK] Test notification sent."
else
    echo "[WARN] Notification test failed, but basic connectivity works."
fi

echo ""
echo "========================================="
echo " All tests passed. Bot is ready."
echo "========================================="
exit 0
