"""Lynceus search API. Thin layer over search.py: no search logic lives here."""

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.search import LynceusIndex, get_embedder, load_field_map, load_records

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = os.getenv("LYNCEUS_CORPUS", str(ROOT / "Data" / "Cleaned_data"))
ENRICHED_DIR = os.getenv("LYNCEUS_ENRICHED", str(ROOT / "Data" / "enriched"))
FIELD_MAP = os.getenv("LYNCEUS_FIELD_MAP", str(ROOT / "field_map.json"))
TEST_SET = os.getenv("LYNCEUS_TEST_SET", str(ROOT / "evaluation" / "test_set.json"))

# All routes live under /api, which is where the frontend calls them.
router = APIRouter(prefix="/api", tags=["search"])
_state: dict = {"index": None}


def build() -> LynceusIndex:
    recs = load_records(CORPUS_DIR, ENRICHED_DIR, load_field_map(FIELD_MAP))
    _state["index"] = LynceusIndex(recs, get_embedder(os.getenv("LYNCEUS_EMBEDDER", "auto")))
    return _state["index"]


def index() -> LynceusIndex:
    return _state["index"] or build()


def normalise_case_id(raw: str) -> str:
    """Accept '746', 'case-746', 'CASE-746', 'case_746' or 'case-746.txt'."""
    dash_chars = "‐‑‒–—―−"
    s = raw.strip().lower().translate(str.maketrans({char: "-" for char in dash_chars}))
    if s.endswith(".txt"):
        s = s[:-4]
    s = s.replace("_", "-").replace(" ", "-")
    return s if s.startswith("case-") else f"case-{s}"


def _record(case_id: str):
    wanted = normalise_case_id(case_id)
    for r in index().records:
        if r.case_id.lower() == wanted:
            return r
    raise HTTPException(status_code=404, detail=f"{case_id} not found")


def _enrichment_files(case_id: str) -> tuple[dict | None, dict | None]:
    active_dir = Path(ENRICHED_DIR)
    draft_dir = active_dir.parent / f"{active_dir.name}_draft"

    def read(path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    return read(active_dir / f"{case_id}.json"), read(draft_dir / f"{case_id}.json")


ENRICHMENT_FIELDS = ("language", "sector", "country", "problem_plain",
                     "capability", "scale_outcomes", "reusable")
NO_MATCH_MESSAGE = ("No strong match found in past deliveries for this question. "
                    "Try rephrasing, or this may be new work for us.")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The lead's need in plain English")
    k: int = Field(5, ge=1, le=10)


def _for_frontend(out: dict) -> dict:
    """Shape a search result the way frontend/src/api/search.ts expects it,
    keeping why/strong_match/score so the UI can explain each result."""
    by_id = {r.case_id: r for r in index().records}
    results = []
    for res in out["results"]:
        rec = by_id[res["case_id"]]
        active_record, _ = _enrichment_files(rec.case_id)
        agent_meta = (active_record or {}).get("_agent", {})
        results.append({
            "case_id": res["case_id"],
            "enriched": bool(rec.fields),
            "reviewed_by_human": bool(agent_meta.get("reviewed_by_human", False)),
            "rank": res["rank"],
            "score": res["score"],
            "similarity": res["similarity"],
            "strong_match": res["strong_match"],
            "summary": res["summary"],
            "why": res["why"],
            "source_path": f"/api/cases/{res['case_id']}",
            "source_file": Path(rec.source_path).name,
            **{f: rec.fields.get(f, "") for f in ENRICHMENT_FIELDS},
        })
    return {
        "query": out["query"],
        "results": results,
        "message": NO_MATCH_MESSAGE if out["no_strong_match"] else None,
        "no_strong_match": out["no_strong_match"],
        "corrections": out["corrections"],
        "embedder": out["embedder"],
    }


@router.post("/search")
def search_post(body: SearchRequest):
    """What the frontend calls: POST /api/search with {"query": "..."}."""
    return _for_frontend(index().search(body.query.strip(), k=body.k))


@router.get("/search")
def search_get(q: str = Query(..., min_length=3, description="The lead's need in plain English"),
               k: int = Query(5, ge=1, le=10)):
    """Same as POST, handy for curl and the /docs page."""
    return _for_frontend(index().search(q.strip(), k=k))


@router.get("/cases")
def list_cases():
    """Every indexed case: id, source file, language (if enriched), enriched or not."""
    return [{"case_id": r.case_id,
             "source_file": Path(r.source_path).name,
             "language": r.fields.get("language") or None,
             "enriched": bool(r.fields)}
            for r in index().records]


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    """The source entry: original text plus its enrichment, for tracing claims."""
    r = _record(case_id)
    enrichment, draft = _enrichment_files(r.case_id)
    return {"case_id": r.case_id,
            "source_file": Path(r.source_path).name,
            "text": r.raw_text,
            "enrichment": enrichment,
            "draft": draft}


@router.get("/cases/{case_id}/similar")
def similar_cases(case_id: str, k: int = Query(3, ge=1, le=10)):
    """'More like this': other deliveries closest to this one."""
    rec = _record(case_id)
    out = index().similar(rec.case_id, k=k)
    for r in out["results"]:
        r["source_url"] = f"/api/cases/{r['case_id']}"
    return out


@router.post("/reindex")
def reindex():
    """Reload corpus and enrichment, e.g. after the live-round files arrive.
    Only new or changed texts are re-embedded."""
    idx = build()
    return {"cases": len(idx.records),
            "enriched": sum(1 for r in idx.records if r.fields),
            "embedder": idx.embedder.name if idx.embedder else "none"}


@router.get("/status")
def status():
    """What's loaded right now: useful at the start of the demo."""
    idx = index()
    return {"cases": len(idx.records),
            "enriched": sum(1 for r in idx.records if r.fields),
            "not_enriched": [r.case_id for r in idx.records if not r.fields],
            "embedder": idx.embedder.name if idx.embedder else "none"}


@router.get("/evaluate")
def evaluate(k: int = Query(3, ge=1, le=10)):
    """Run the test set: top-k hit per question and overall hit rate."""
    path = Path(TEST_SET)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"test set not found: {path}")
    tests = json.loads(path.read_text(encoding="utf-8"))
    idx = index()
    idx.prime_queries([t["question"] for t in tests])
    rows, hits = [], 0
    for t in tests:
        out = idx.search(t["question"], k=k)
        got = [r["case_id"] for r in out["results"]]
        ok = all(e in got for e in t["expected"]) if t["expected"] else out["no_strong_match"]
        hits += ok
        rows.append({"id": t.get("id"), "question": t["question"], "expected": t["expected"],
                     "returned": got, "hit": ok, "no_strong_match": out["no_strong_match"],
                     "top_strength": out["top_strength"]})
    return {"k": k, "hit_rate": round(hits / len(tests), 3), "hits": hits,
            "total": len(tests), "embedder": out["embedder"], "questions": rows}
