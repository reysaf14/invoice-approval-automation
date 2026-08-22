# ADR-005: Webhook Authentication - HMAC Signature + Shared Secret

## Status
Accepted

## Context
Two webhook endpoints receive external callbacks:
1. Telegram callback (Approve/Reject button clicks) → n8n webhook
2. Google Doc AI async callback (if using batchProcess) → n8n webhook

Need to prevent unauthorized invocation, replay attacks, and ensure payload integrity.

## Decision
Use **HMAC-SHA256 signature verification** with a shared secret for all incoming webhooks.

## Alternatives Considered
1. **IP Whitelist** - Simple but fragile (Telegram/GCP IPs change), no payload integrity
2. **Shared Secret in Query Param** - Exposed in logs, no replay protection
3. **JWT** - Overkill for internal webhooks, key management complexity
4. **No Auth (Security by Obscurity)** - Unacceptable for financial data

## Consequences
- **Positive**: Strong integrity + authenticity, replay protection via timestamp, standard algorithm, low overhead
- **Negative**: Need to manage secret rotation, n8n workflow must verify before processing, clock sync required (±5 min)
- **Risk**: Secret leaked → rotate immediately; clock drift → reject valid requests

## Implementation Details

### Secret Generation
```bash
# Generate 32-byte secret
openssl rand -hex 32
# Store in n8n credentials as "WEBHOOK_HMAC_SECRET"
```

### Telegram Webhook Payload
```
POST /webhook/approve
Headers:
  X-Signature: sha256=<hmac_sha256(secret, payload + "." + timestamp)>
  X-Timestamp: <unix_epoch_seconds>
Body: {"invoice_id": "uuid", "action": "approve|reject", "reason": "..."}
```

### Verification Logic (n8n Function Node)
```javascript
const secret = $credentials.webhookHmacSecret;
const timestamp = $request.headers['x-timestamp'];
const signature = $request.headers['x-signature'];
const payload = JSON.stringify($request.body);

// Replay protection: reject if timestamp > 5 min old
if (Math.abs(Date.now()/1000 - timestamp) > 300) {
  throw new Error('Timestamp expired');
}

// Verify HMAC
const expected = 'sha256=' + crypto.createHmac('sha256', secret)
  .update(payload + '.' + timestamp)
  .digest('hex');

if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
  throw new Error('Invalid signature');
}

// Valid - continue workflow
return $request.body;
```

### Google Doc AI Callback (if async)
Same pattern, different endpoint: `/webhook/doc-ai-callback`
Payload includes `operation_id`, `status`, `document` reference.

## Secret Rotation
- Rotate every 90 days via n8n credentials update
- Overlap period: accept both old + new for 24h during rotation
- Audit log all rotation events