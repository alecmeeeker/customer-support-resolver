# Customer Support Resolver

An end-to-end pipeline that ingests customer emails, classifies them by business context, and resolves support issues by finding semantically similar past cases and synthesizing fix instructions using LLM.

## What It Does

Customer support teams deal with recurring issues. This system automates the pattern: when a new complaint arrives, it searches a vector database of previously resolved issues, ranks them by semantic similarity, and generates actionable resolution steps — combining insights from multiple similar cases into a single suggested fix.

**Pipeline stages:**

1. **Extract** — Pulls emails from Gmail via OAuth2 with full threading and participant metadata
2. **Deduplicate** — Fingerprints emails using content normalization (URL/email replacement, alias resolution, forward/reply chain parsing) to eliminate exact and near-duplicates
3. **Chunk & Embed** — Splits email bodies into 500-character chunks, generates 384-dim vector embeddings with `all-MiniLM-L6-v2`, stores in PostgreSQL via pgvector
4. **Classify** — Assigns business labels using deterministic rules (financial senders, newswire domains, marketing patterns) with Gemini LLM fallback for ambiguous cases. 18 classification categories, multi-label support
5. **Resolve** — Matches incoming customer complaints against resolved issues via cosine similarity search, synthesizes fix documentation from the top-k matches using LLM

## Architecture

```
Gmail (OAuth2)
  |
  v
gmail_oauth_extractor.py ──> PostgreSQL (classified_emails)
  |
  v
email_deduplication_complete.py ──> Fingerprint + deduplicate
  |
  v
batch_process_all_emails.py ──> Chunk + embed (pgvector HNSW)
  |
  v
batch_llm_classifier_optimized.py ──> Classify into pipelines
  |
  v
customer_issue_tracker_v2.py ──> Semantic match + resolution synthesis
  |
  v
customer_issue_dashboard.py ──> Flask dashboard (localhost:5000)
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `gmail_oauth_extractor.py` | Gmail extraction with OAuth2, savepoint-based transaction handling |
| `email_deduplication_complete.py` | Content fingerprinting with multi-language forward/reply parsing |
| `email_normalization.py` | Email content normalization (URL stripping, alias resolution, HTML-to-text) |
| `batch_process_all_emails.py` | Batch chunking and embedding generation (~1800 emails/min) |
| `batch_llm_classifier_optimized.py` | Deterministic rules + Gemini LLM classification with cost tracking |
| `email_pipeline_router.py` | Multi-label routing with priority scoring |
| `enhanced_email_embeddings.py` | Context-enriched embeddings incorporating sender history and thread context |
| `customer_issue_tracker_v2.py` | Semantic similarity search over resolved issues, LLM-powered resolution synthesis |
| `customer_issue_dashboard.py` | Flask web dashboard for issue statistics and resolution tracking |
| `local_oauth_service.py` | Full OAuth2 authorization code flow with Fernet-encrypted token storage |

## Tech Stack

- **Python 3.8+**
- **SQLite** (embedded relational database, zero-config)
- **LanceDB** (embedded vector database for similarity search)
- **sentence-transformers** (`all-MiniLM-L6-v2`, 384 dimensions)
- **Google Gemini API** for classification and resolution synthesis
- **Gmail API** via OAuth2 (with legacy service account support)
- **Flask** for the dashboard
- **cryptography** (Fernet) for secure token storage

## Database

**SQLite** (`data/limrose.db`) — 16 tables for relational data across three domains:

**Email Storage** — `classified_emails`, `email_fingerprints_v2`, `email_duplicate_groups`, `parsed_emails`

**Classification & Routing** — `email_classifications`, `email_pipeline_routes`, `pipeline_outcomes`, `pipeline_context_enrichment`, `classification_performance`

**Issue Resolution** — `customer_issues`, `customer_issues_v2`, `resolution_feedback`, `issue_similarity_cache`, `sender_interaction_history`, `thread_context`

**LanceDB** (`data/vectors/`) — 3 tables for vector embeddings: `email_chunk_vectors`, `enhanced_embedding_vectors`, `issue_embedding_vectors`. Cosine similarity search for semantic matching.

## Setup

### Prerequisites

- Python 3.8+
- Gmail account with Google Cloud project (Gmail API enabled)
- Gemini API key ([get one here](https://makersuite.google.com/app/apikey))

No database installation required — SQLite and LanceDB are embedded and set up automatically.

### Install

```bash
git clone https://github.com/alecmeeeker/customer-support-resolver.git
cd customer-support-resolver

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

```bash
# Copy environment template
cp .env.example .env
# Edit with your credentials (DB_NAME, LLM_API_KEY, etc.)

# Set up Gmail OAuth (interactive browser flow)
python setup_oauth.py

# Create database tables
python scripts/setup_all_tables.py
```

### Run

```bash
# Full pipeline (extract -> deduplicate -> embed -> classify -> resolve)
./update_emails_v2.sh

# Or run stages individually:
python gmail_oauth_extractor.py          # Extract emails
python batch_process_all_emails.py       # Chunk + embed
python batch_llm_classifier_optimized.py --all  # Classify
python customer_issue_tracker_v2.py      # Resolve issues

# View dashboard
python customer_issue_dashboard.py
# Open http://localhost:5000
```

### Verify Installation

```bash
python validate_installation.py
```

## Classification Categories

Emails are multi-labeled into 18 business categories including: `editorial_collaboration`, `freelance_pitch`, `story_lead_or_tip`, `press_release`, `sales_or_advertising_inquiry`, `strategic_partnership`, `legal_or_corporate`, `human_resources`, `financial_admin`, `marketing_or_newsletter`, and others.

Deterministic rules handle high-confidence cases (known financial senders, newswire domains) without API calls. Ambiguous emails fall through to Gemini with token counting and cost tracking.

## Testing

```bash
python test_oauth_core.py    # OAuth import and config tests
python test_oauth_setup.py   # Encryption, port detection, URL generation
python test_oauth_flow.py    # Token storage, refresh logic, file permissions
```

## License

Licensed under the Applequist Open Source License (AOSL). See [LICENSE](LICENSE).

Commercial use requires visible attribution. See [ATTRIBUTION.md](ATTRIBUTION.md) for details.
