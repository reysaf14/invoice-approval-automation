# Setup Guide - Invoice Approval Automation

## Prerequisites

### 1. Infrastructure
- **Docker & Docker Compose** (v2.x)
- **Server/VM** with: 2 CPU, 4GB RAM, 20GB disk (minimum)
- **Domain** (optional, for production webhook URL) or use localhost/ngrok for development

### 2. Google Cloud Project
- **GCP Project** with billing enabled
- **APIs Enabled**:
  - Google Sheets API
  - Google Drive API
  - Document AI API
- **Service Account** with roles:
  - `roles/editor` (or minimal: Sheets Editor, Drive File Admin, Document AI API User)
  - Download JSON key → save as `credentials/sa-key.json`

### 3. Google Document AI Processor
1. Go to **Document AI** → **Processors** → **Create Processor**
2. Type: **Enterprise Document OCR**
3. Region: `asia-southeast1` (Jakarta) - recommended for latency
4. Note: `PROJECT_ID`, `LOCATION`, `PROCESSOR_ID`
5. **Free tier**: 1,000 pages/month for 3 months (new accounts)

### 4. Google OAuth Credentials (for n8n)
1. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth Client ID**
2. Type: **Web Application**
3. Authorized redirect URIs:
   - `http://localhost:5678/oauth2/callback` (dev)
   - `https://your-domain.com/oauth2/callback` (prod)
4. Note: `CLIENT_ID`, `CLIENT_SECRET`

### 5. Google Sheets & Drive Setup
1. Create **Spreadsheet** for invoice master data
2. Share with Service Account email (Editor)
3. Note: `SPREADSHEET_ID` (from URL)
4. Create **Drive Folder**: `Invoices_Incoming`
5. Share with Service Account (Editor)
6. Note: `FOLDER_ID` (from URL)

### 6. Telegram Bot
1. Message **@BotFather** → `/newbot`
2. Note: `BOT_TOKEN`
3. Get **Chat IDs**:
   - Owner: Message bot → `@userinfobot` → forward to bot
   - Admin: Same process
4. Set webhook (after n8n running):
   ```bash
   curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d "url=https://your-domain.com/webhook/telegram"
   ```

---

## Installation Steps

### 1. Clone & Configure
```bash
cd invoice-approval-automation
cp .env.template .env
# Edit .env with all values from prerequisites
```

### 2. Prepare Credentials
```bash
mkdir -p credentials
# Place Google Service Account key:
cp /path/to/sa-key.json credentials/sa-key.json
chmod 600 credentials/sa-key.json
```

### 3. Generate Secrets
```bash
# HMAC secret for webhook auth
openssl rand -hex 32
# Add to .env as WEBHOOK_HMAC_SECRET

# Strong passwords for n8n & PostgreSQL
openssl rand -base64 24
# Add to .env as N8N_BASIC_AUTH_PASSWORD, DB_POSTGRES_PASSWORD
```

### 4. Start Services
```bash
# Development
docker-compose up -d

# Production (with domain)
# Ensure .env has correct WEBHOOK_URL (https://your-domain.com/webhook)
docker-compose -f docker-compose.yml up -d
```

### 5. Verify Services
```bash
# Check logs
docker-compose logs -f n8n

# Health checks
curl http://localhost:5678/healthz
curl http://localhost:5678/webhook/health  # if you add a health endpoint
```

### 6. n8n Initial Setup
1. Open `http://localhost:5678`
2. Login with `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`
3. **Credentials** → **New Credential** → Add:
   - **Google OAuth2 API**: Use `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - **Telegram API**: Use `TELEGRAM_BOT_TOKEN`
   - **Header Auth** (for HMAC): Name `WEBHOOK_HMAC_SECRET`, Value from `.env`
4. **Workflows** → **Import** → Load `n8n-workflows/01-invoice-ingestion.json`, `02-approval-handler.json`, `03-reminder-escalation.json`
5. Configure each workflow's credentials (Google, Telegram, HMAC)
6. Activate all workflows

### 7. Test End-to-End
1. Upload test invoice (PDF/image) to `Invoices_Incoming` Drive folder
2. Check n8n executions: `01-invoice-ingestion` should run
3. Verify row added to Google Sheets (status: "Pending Approval")
4. Check Telegram: Owner should receive notification with buttons
5. Click **Approve** → Form opens → Submit
6. Verify Sheets status → "Approved", Admin gets notification

---

## Directory Structure

```
invoice-approval-automation/
├── docker-compose.yml
├── .env                    # Actual secrets (gitignored)
├── .env.template           # Template
├── credentials/
│   └── sa-key.json         # Google Service Account (gitignored)
├── n8n-workflows/
│   ├── 01-invoice-ingestion.json
│   ├── 02-approval-handler.json
│   └── 03-reminder-escalation.json
└── docs/
    ├── SETUP.md
    ├── OPERATIONS.md
    └── USER_GUIDE.md
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| n8n won't start | Check `docker-compose logs n8n` - usually PostgreSQL not ready or port conflict |
| Google API 403 | Verify Service Account has correct roles, Sheet/Drive shared with SA email |
| Doc AI 404 | Check `PROCESSOR_ID`, `LOCATION`, `PROJECT_ID` match exactly |
| Telegram webhook fails | Verify `WEBHOOK_URL` accessible from internet (use ngrok for dev) |
| Sheets not updating | Check n8n Google credentials connected, workflow active |
| HMAC verification fails | Ensure `WEBHOOK_HMAC_SECRET` matches in .env and n8n credentials |

---

## Production Checklist

- [ ] Use HTTPS domain (reverse proxy: Nginx/Traefik + Let's Encrypt)
- [ ] Set `N8N_PROTOCOL=https`, `WEBHOOK_URL=https://...`
- [ ] Strong passwords in `.env`
- [ ] Regular PostgreSQL backups (cron: `pg_dump`)
- [ ] Monitor disk space (n8n executions, PostgreSQL, Redis)
- [ ] Set up log aggregation (Loki, ELK, or simple file rotation)
- [ ] Document AI: Monitor usage, set budget alerts in GCP
- [ ] Telegram: Set webhook to production URL
- [ ] Rotate `WEBHOOK_HMAC_SECRET` every 90 days