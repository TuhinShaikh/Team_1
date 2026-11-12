# Lynceus frontend

The frontend is a React and TypeScript single-page app built with Vite. It provides project search, case analysis, and the all-documents view.

## Run locally

From the repository root, start the API in one terminal:

```bash
python -m uvicorn backend.main:app --reload
```

Then start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally <http://localhost:5173>). The API must be available at <http://localhost:8000>.

See the [root README](../README.md) for Python setup, API keys, project structure, and data preparation.

## Build

```bash
npm run build
```

Vite writes the production build to `dist/`.
