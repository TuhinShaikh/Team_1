# Lynceus

Lynceus helps users find relevant past project cases by describing a client need. It combines keyword search with optional multilingual semantic search, and shows the source case so users can check the evidence. The web app also provides a browsable list of case documents and case analysis.

## Project layout

```text
frontend/              React + TypeScript interface, built with Vite
project_backend/       FastAPI application entry point
search.py              Hybrid search and indexing logic
routers/               Search, case, and document API routes
Data/Original_data/    Original case text files
Data/Cleaned_data/     Normalized case text used for indexing
Data/enriched/         Structured case fields used to improve search
scripts/               Data cleaning and corpus generation
evaluation/            Search evaluation questions
```

## Requirements

- Python 3.10 or newer
- Node.js 20.19+ or 22.12+ (required by the Vite version in this project)
- npm (included with Node.js)

## Start the application

Run the backend and frontend in two separate terminals from the repository root.

### 1. Start the FastAPI backend

Create and activate a virtual environment, then install the Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Start the API from the repository root:

```bash
python -m uvicorn project_backend.main:app --reload
```

The API runs at <http://localhost:8000>. Interactive API documentation is at <http://localhost:8000/docs>; the health check is <http://localhost:8000/health>.

### 2. Start the React frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually <http://localhost:5173>. The frontend calls the API at `http://localhost:8000`, so keep the backend running while using the app.

## API keys and search modes

The app can start without API keys. By default, search uses BM25 keyword matching. To enable multilingual semantic retrieval, create a `.env` file in the repository root and set a Voyage key:

```dotenv
VOYAGE_API_KEY=your-voyage-api-key
```

`ANTHROPIC_API_KEY` is needed for AI-generated case analysis and agent answers. Add it to the same `.env` file to use those features:

```dotenv
ANTHROPIC_API_KEY=your-anthropic-api-key
```

The backend reads `.env` at startup. Restart it after changing the file. Do not commit real API keys.

## What the app does

- **Search projects:** Submit a plain-language description to find similar cases. Results include match explanations and links to the source material. Use the reload action after changing corpus or enrichment files.
- **All documents:** Browse the available case documents.
- **Case analysis:** View case observations and an overall assessment. An Anthropic key enables a generated analysis; otherwise, saved enrichment or source-text fallback may be returned.
- **Search API:** `POST /api/search`, `GET /api/search`, `GET /api/cases`, `GET /api/cases/{case_id}`, `GET /api/cases/{case_id}/similar`, `GET /api/status`, `POST /api/reindex`, and `GET /api/evaluate`.
- **Other API routes:** `GET /endpoints/documents`, `GET /endpoints/{case_id}`, and `POST /endpoints/ask`.

## Data preparation

The checked-in cleaned case files are ready to use. If you add or replace original case text and need to regenerate the cleaned files and corpus, run this from the repository root:

```bash
python scripts/run_pipeline.py
```

The pipeline reads `Data/Original_data/` and `lynceus_answer_key_file_map.csv`, then updates `Data/Cleaned_data/`, `Data/manifest.csv`, `Data/quality_report.csv`, and `Data/corpus.py`. Original files are not modified. Restart the backend or call `POST /api/reindex` to load changed data into the running search index.

## Frontend production build

```bash
cd frontend
npm run build
```

The generated static files are written to `frontend/dist/`.
