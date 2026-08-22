# ADR-002: OCR Provider - Google Document AI Enterprise OCR

## Status
Accepted

## Context
Need to extract 4 fields (Vendor, Date, Invoice Number, Amount) from PDF and image invoices (photos from WhatsApp). Volume: ~180 pages/month. Must integrate with Google Workspace ecosystem. Cost sensitivity: freelance project budget.

## Decision
Use **Google Document AI - Enterprise Document OCR Processor** as primary OCR.

## Alternatives Considered
1. **Gemini 1.5 Flash** - Cheaper (~$0.05/mo), flexible prompt, but requires prompt engineering and JSON parsing
2. **GPT-4o-mini** - Good vision, structured output, but ~$0.20-0.50/mo and external vendor
3. **AWS Textract Analyze Expense** - Invoice-specialized, but $30/1K pages ($2.40/mo), AWS lock-in
4. **Local models (Donut/LayoutLM)** - Free but requires GPU, maintenance, lower accuracy on varied formats

## Consequences
- **Positive**: Native GCP integration, 1,000 pages/month free tier (covers current volume), $1.50/1K pages after, high accuracy for Indonesian invoices, managed service, no GPU needed
- **Negative**: Requires GCP project + billing setup, processor creation in specific region, less flexible than LLM prompts for unusual formats
- **Risk**: Free tier is 3 months for new accounts only → plan for $0.27/mo after free tier expires

## Implementation Notes
- Create processor in `asia-southeast1` (Jakarta) or `us-central1` for latency
- Use `process` endpoint (synchronous) for single-page, `batchProcess` for multi-page
- Parse `document.entities` for structured extraction
- Confidence scores available per entity
- Fallback: If confidence < 0.85 → flag for manual review (status: "Low Confidence")