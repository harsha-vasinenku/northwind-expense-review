# Northwind Expense Review System

AI-powered expense compliance reviewer for Northwind Logistics. Extracts receipt data, retrieves relevant policy clauses via RAG, and returns a structured verdict using Claude's tool-use API.

---

## Quick Start (5 minutes)

```bash
git clone <repo-url>
cd northwind-expense-review

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

docker-compose up
# Open http://localhost:3000
```

**Without Docker:**
```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env   # add your key
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## Architecture

```
┌─────────────┐    REST/JSON     ┌──────────────────────────────────────────┐
│  React SPA  │ ──────────────► │  FastAPI Backend                          │
│  (Vite +    │                  │                                            │
│  Tailwind)  │                  │  ┌──────────┐  ┌──────────┐  ┌────────┐  │
└─────────────┘                  │  │ ingestion│  │  verdict │  │  RAG   │  │
                                 │  │ service  │  │  engine  │  │service │  │
                                 │  └────┬─────┘  └────┬─────┘  └───┬────┘  │
                                 │       │              │            │        │
                                 │       ▼              ▼            ▼        │
                                 │  ┌─────────────────────┐  ┌───────────┐  │
                                 │  │  Anthropic Claude    │  │ ChromaDB  │  │
                                 │  │  (claude-sonnet-4-6) │  │  (policy  │  │
                                 │  └─────────────────────┘  │   index)  │  │
                                 │                            └───────────┘  │
                                 │  ┌────────────────────────────────────┐   │
                                 │  │  SQLite (employees, submissions,   │   │
                                 │  │  line_items, overrides, audit_logs)│   │
                                 │  └────────────────────────────────────┘   │
                                 └──────────────────────────────────────────┘
```

**Data flow for a receipt upload:**
1. File arrives via multipart POST
2. PDF text extracted (pdfplumber) or OCR'd via Claude vision
3. `extract_receipt_data` tool call → structured receipt fields
4. ChromaDB queried with expense category + vendor → top-5 policy chunks
5. `submit_expense_verdict` tool call with receipt + employee context + policy clauses
6. Structured verdict stored in SQLite line_items table

---

## Design Decisions

### Section-level chunking vs token-level
Policy documents are split at section headings (e.g. `§3.1`, `2.1.`), not at arbitrary token counts. This preserves the semantic unit of each rule — a clause about meal caps should not be split across two chunks. Section-level chunks also produce deterministic IDs (`TEP-001-3_1`) enabling idempotent re-indexing.

### Tool-use API vs prompt + regex parsing
Claude's tool-use API forces a JSON schema on the output. This eliminates all regex parsing of free-text verdict responses, making the pipeline deterministic and auditable. If Claude cannot call the tool (e.g., malformed input), the system catches it and returns `needs_review` with `confidence=0.0` — never silently producing garbage.

### SQLite vs PostgreSQL
SQLite with `aiosqlite` is sufficient for this workload (single-instance, sub-second queries, no concurrent writers). It requires zero infrastructure setup — the database is a single file that persists across restarts. For production at scale, the `DATABASE_URL` env var can point to PostgreSQL without code changes (SQLAlchemy abstracts the dialect).

### Vision model for image receipts vs text-only
JPG/PNG receipts always go through Claude's vision capability. PDFs use pdfplumber first; if extracted text is sparse (<50 chars), they fall back to vision. This handles scanned PDFs and photo receipts uniformly without a separate OCR service.

### Confidence calibration
- `≥0.9`: controlling policy clause explicitly retrieved and applicable
- `0.6–0.9`: policy retrieved but ambiguous (e.g., grade-based caps inferred rather than stated)
- `<0.6`: policy absent or retrieval returned only noise documents

The verdict engine is instructed: *"If the controlling policy is not present, set verdict to 'needs_review' and confidence below 0.6."* This means missing policies always surface as low-confidence `needs_review` rather than confident incorrect verdicts.

### Missing policies
`ALL_TE_POLICY_IDS` lists every T&E policy the system knows *should* exist. On each verdict call, the engine computes which are absent from ChromaDB and injects them as a `MISSING POLICIES` section in the prompt. Claude then acknowledges the gap when issuing the verdict.

### Flagged vs needs_review
- `flagged` = specific, citable policy clause violated (e.g., "TEP-005 §2.1 states economy class for domestic; business class charged")
- `needs_review` = policy exists but is ambiguous, OR the relevant policy is missing from the indexed documents, OR the receipt has anomalies Claude cannot resolve without human judgment

---

## Cost Analysis

**Per submission (average 7 receipts):**
- Extraction: ~1,500 input tokens + ~300 output tokens per receipt × 7 = ~12,600 input / ~2,100 output
- Verdict: ~3,000 input tokens + ~400 output tokens per receipt × 7 = ~21,000 input / ~2,800 output
- Total per submission: ~33,600 input / ~4,900 output tokens
- At claude-sonnet-4-6 pricing (~$3/MTok in, ~$15/MTok out): **~$0.17/submission**

**At 10,000 submissions/day:**
- ~$1,700/day (~$51,000/month)
- Optimization: cache policy chunks in prompt cache (~90% input token reduction on the policy section)

---

## What's Next

1. **Prompt caching** — the policy clause section is static per category; caching would cut per-call cost by ~70%
2. **Parallel receipt processing** — current implementation processes receipts sequentially; `asyncio.gather()` across all receipts in a submission would cut wall-clock time by ~7×
3. **PostgreSQL + connection pooling** — for multi-instance deployments
4. **Grade-based policy resolution** — TEP-009 defines grade tiers but the verdict engine currently passes grade as context; a structured lookup table would make grade-based rules more reliable
5. **Receipt deduplication by visual hash** — current dedup uses SHA-256 of file bytes; a perceptual hash would catch re-scanned receipts
6. **Alembic migrations** — currently using `create_all()` at startup; migration history needed for production schema changes
7. **Fine-tuned confidence calibration** — collect human labels on `needs_review` cases, train a calibration layer

---

## Eval Harness

```bash
# From project root, with server running:
cd backend
python ../eval/harness.py --fixture ../eval/fixtures/expected_outcomes_sample.json

# Custom base URL:
python ../eval/harness.py \
  --fixture ../eval/fixtures/expected_outcomes_sample.json \
  --base-url https://your-deployed-url.railway.app
```

The harness creates real submissions via the API, uploads actual receipt PDFs, and scores:
- **Verdict accuracy** (compliant/flagged/needs_review)
- **Flag detection** (alcohol_on_solo_trip, over_meal_cap, etc.)
- **Citation faithfulness** (does cited clause mention the relevant keyword?)
- **Refusal rate** (out-of-scope Q&A questions correctly declined)
- **Q&A answer quality** (does the answer cite the correct policy doc?)
