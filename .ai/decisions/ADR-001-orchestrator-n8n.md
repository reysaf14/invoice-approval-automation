# ADR-001: Orchestrator Selection - n8n Self-Hosted via Docker

## Status
Accepted

## Context
Project requires orchestration of multi-step workflow: file detection (Gmail/Drive) → OCR extraction → deduplication → Google Sheets write → Telegram notification → approval handling → status update → admin notification → reminders. Volume is low (~120 invoices/month). Team prefers Google Workspace ecosystem.

## Decision
Use **n8n self-hosted via Docker** as the primary orchestrator.

## Alternatives Considered
1. **Custom Python scripts + cron/Cloud Scheduler** - More control, but higher development/maintenance effort for SaaS integrations
2. **GitHub Actions / GitLab CI** - Not designed for long-running workflows with human-in-the-loop
3. **n8n Cloud** - Recurring cost, less control over data residency
4. **Zapier / Make** - Vendor lock-in, cost scales with tasks, limited custom logic

## Consequences
- **Positive**: Visual workflow builder, 400+ integrations (Gmail, Drive, Sheets, Telegram native), self-hosted (data control), queue mode with Redis for reliability, webhook support for approval callbacks
- **Negative**: Additional infrastructure (PostgreSQL, Redis), learning curve for complex expressions, memory usage ~512MB-1GB
- **Risk**: n8n version upgrades may break workflows → pin version in docker-compose

## Implementation Notes
- Run in queue mode (main + workers) for production reliability
- Use PostgreSQL for execution history, Redis for queue
- Store workflows as JSON in `n8n-workflows/` for version control
- Credentials managed via n8n UI (encrypted in DB), not in workflow JSON