# SchemeSathi – India's Government Benefits Navigator

SchemeSathi is an AI-powered navigator that helps citizens discover, understand, and track eligibility for Indian government schemes. It follows the safety-first principles: never guarantees eligibility/approval, always cites official sources, and requires explicit consent.

## Architecture
- Frontend: Next.js 15 (App Router) + TailwindCSS + TypeScript
- Backend: FastAPI (Python) 
- DB: PostgreSQL (via SQLAlchemy)
- Storage: Private object storage (local/S3-compatible)
- AI/Web: TinyFish (Search/Fetch/Agent), Gemini (optional), OCR (Tesseract/Cloud)

## Quick Start
### Backend
```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # fill keys
uvicorn app.main:app --reload
```

### Frontend
```bash
cd apps/web
npm install
npm run dev
```

## Key Features (MVP)
- Consent-gated flow, privacy-first
- Document upload + OCR with user confirmation
- Profile fact store with provenance
- TinyFish-powered discovery of official schemes
- Deterministic eligibility rules engine with explanations
- Evidence traceability (source URLs, timestamps)
- Monitoring + change detection (simulated/manual check)
- Disclaimers throughout

## API Key
TinyFish: sk-tinyfish-Ee6okripXa8DLjslLHZKtNEPb_CVC7Jl (provided)
Configure in `apps/api/.env`
