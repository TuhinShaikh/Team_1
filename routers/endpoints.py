from anthropic import APIStatusError, APITimeoutError, RateLimitError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

import agent_settings as agent
import llm
from corpus import DOCUMENTS
from routers.search_api import _record  # same case lookup as /api/cases/{id}

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


# ENDPOINT 1 - all documents from the corpus (initial testing; may not be used in production)

@router.get("/documents")
def get_documents():
    """Get all documents from the corpus."""
    return DOCUMENTS


# ENDPOINT 2 - AGENT ASK: the agent answers using the search tool and cites case ids

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


@router.post("/ask")
def ask(req: AskRequest):
    try:
        return agent.ask_with_tools(req.question)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI Agent timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="AI Agent rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="AI Agent unavailable")


# ENDPOINT 3 - LLM ANALYSE ONE CASE by case_id (accepts case-209, 209, CASE-209, case-209.txt)

@router.post("/cases/{case_id}/analyse")
def analyse_case(case_id: str, save: bool = False):
    """Agent draft of the structured English record for one case.
    save=true also writes it to data/enriched/ (plus an untouched draft copy in
    data/enriched_draft/); call POST /api/reindex afterwards so search uses it.
    A person should check the draft against the source before saving."""
    rec = _record(case_id)  # 404 if unknown
    try:
        result = llm.analyse_case(rec.case_id, rec.raw_text)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Summary provider timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Summary provider rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="Summary provider unavailable")
    except (ValidationError, StopIteration):
        raise HTTPException(status_code=502, detail="Model output did not match the required schema")

    if save:
        result["saved_to"] = str(llm.save_enrichment(result, rec.source_path))
    return result