# Operations Guide - Invoice Approval Automation

## n8n API Reference

### Workflow Activation
```bash
# Activate workflow (CORRECT endpoint - PATCH not allowed)
POST /api/v1/workflows/{workflowId}/activate

# Example:
curl -X POST http://localhost:5678/api/v1/workflows/iAbSuXdKGW0DzVdV/activate \
  -H "Authorization: Bearer <N8N_API_KEY>" \
  -H "Content-Type: application/json"

# Note: PATCH /api/v1/workflows/{id} returns 405 (Method Not Allowed)
```

### Workflow Import
```bash
# Import via CLI (sets active=false always)
docker-compose exec n8n n8n import:workflow --input=/path/to/workflow.json

# Delete duplicate workflows after re-import
# Must delete from n8n UI or via API
```

---

## Daily Operations

### Monitoring (Run Daily)
```bash
# Check container health
docker-compose ps

# Check n8n executions (last 24h)
docker-compose exec n8n n8n list:executions --last=24h

# Check failed executions
docker-compose exec n8n n8n list:executions --status=error --last=24h

# View logs
docker-compose logs --tail=100 n8n
docker-compose logs --tail=100 n8n-worker
```

### Google Sheets Checks
- Open master spreadsheet → verify new rows added
- Filter by `Status = "Pending Approval"` → check aging (>24h)
- Filter by `Status = "Failed"` / `"Low Confidence"` → investigate

### Telegram Bot Health
- Send `/start` to bot → should respond
- Check Owner/Admin received test notification

---

## Weekly Operations

### 1. Accuracy Audit (Manual Sample)
- Pick 10 random invoices from Sheets
- Compare extracted fields vs original file in Drive
- Track accuracy % → target ≥ 95%
- If < 95%: Review Doc AI processor, consider custom processor training

### 2. Volume & Cost Review
- Count invoices processed this week (Sheets row count)
- Check Document AI usage in GCP Console → Billing
- Verify within free tier or expected cost

### 3. Reminder Effectiveness
- Check `reminder_count` distribution in Sheets
- % approved before 1h, 4h, 12h, 24h
- Escalations triggered (>24h pending)

### 4. Duplicate Rate
- Count `Status = "Duplicate"` / Total processed
- If > 5%: Investigate source (supplier double-send, Admin double-forward)

---

## Monthly Operations

### 1. Archive Old Data
```bash
# In Google Sheets:
# 1. Filter Created_At < 2 years ago
# 2. Copy to new sheet: Invoices_Archive_YYYY
# 3. Delete from master (keep last 2 years)
```

### 2. Secret Rotation (Every 90 Days)
```bash
# Generate new HMAC secret
openssl rand -hex 32
# Update .env and n8n credentials (Header Auth)
# Overlap: Keep old secret valid for 24h during transition
```

### 3. n8n Version Update
```bash
# Check current version
docker-compose exec n8n n8n --version

# Update (pin major version in docker-compose.yml)
# image: n8nio/n8n:1.XX.X
docker-compose pull
docker-compose up -d
```

### 4. Backup Verification
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U n8n n8n > backup_$(date +%Y%m%d).sql

# Verify backup restorable (test on staging)
```

---

## Incident Response

### Scenario: Ingestion Stops (No new rows in Sheets)
1. Check `docker-compose ps` - all containers running?
2. Check n8n executions: `docker-compose exec n8n n8n list:executions --status=error --last=1h`
3. Check Gmail/Drive trigger logs in n8n UI
4. Common causes:
   - Google OAuth token expired → Reconnect credentials in n8n
   - Drive folder permission changed → Re-share with Service Account
   - Doc AI quota exceeded → Check GCP billing

### Scenario: Approval Not Working (Owner clicks, no update)
1. Check n8n executions for `02-approval-handler` - errors?
2. Verify webhook URL accessible: `curl -X POST <WEBHOOK_URL>/approve/test`
3. Check HMAC secret matches in .env and n8n credentials
4. Check Telegram callback format hasn't changed

### Scenario: High "Low Confidence" Rate
1. Sample failed invoices - check image quality (blur, rotation, crop)
2. Consider: Pre-processing (auto-rotate, enhance) before Doc AI
3. Or: Train custom Doc AI processor with 50+ samples

### Scenario: Duplicate Invoices Not Caught
1. Verify composite key logic: vendor + invoice_number + date + amount
2. Check for whitespace/case differences in source data
3. Add normalization in n8n (trim, lower) before dedupe check

---

## Scaling Considerations

| Metric | Current | Threshold | Action |
|--------|---------|-----------|--------|
| Invoices/month | ~120 | > 500 | Add PostgreSQL for business data, keep Sheets for UI |
| Concurrent approvals | < 5 | > 20 | Increase n8n workers, Redis memory |
| Doc AI pages/month | ~180 | > 1,000 | Monitor cost, consider custom processor |
| Sheets rows | ~1,400/yr | > 50,000 | Archive yearly, consider BigQuery |

---

## Log Locations

| Component | Location |
|-----------|----------|
| n8n Main | `docker-compose logs n8n` |
| n8n Worker | `docker-compose logs n8n-worker` |
| PostgreSQL | `docker-compose logs postgres` |
| Redis | `docker-compose logs redis` |
| n8n Internal | n8n UI → Executions (stored in PostgreSQL) |

---

## Useful Commands

```bash
# Restart single service
docker-compose restart n8n

# Rebuild after config change
docker-compose up -d --build n8n

# View real-time logs
docker-compose logs -f n8n

# Execute command in container
docker-compose exec n8n sh

# PostgreSQL shell
docker-compose exec postgres psql -U n8n -d n8n

# Redis CLI
docker-compose exec redis redis-cli

# Clean up (WARNING: destroys data)
docker-compose down -v
```