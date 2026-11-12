

## lynceus project


# HOW TO RUN THE SERVER 

This is how to run fast api



1. CD to project_backend folder  in git bash


2. Create virtual enviroment in git bash 

 $ python -m venv venv


3. Activate virtual enviroment in git bash 

 $ source venv/Scripts/activate

4. Install requirements.text  in git bash 

 $ pip install -r requirements.txt


5. Run server with 

 $ uvicorn main:app --reload


The backend now serves the hybrid search API from the repository (`/api/search`,
`/api/status`, `/api/reindex`, and `/api/evaluate`) as well as the case and
document endpoints. Search starts without an Anthropic key. Set
`VOYAGE_API_KEY` to enable multilingual semantic retrieval; without an embedder,
search falls back to BM25 keyword matching. `ANTHROPIC_API_KEY` is only needed
for agent answers and generated case enrichment. Copy the repository's
`.env.example` to `.env` and add the keys there; the backend loads that file at
startup.
