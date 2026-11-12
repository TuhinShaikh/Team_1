from anthropic import APIStatusError, APITimeoutError, RateLimitError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError
import re

import agent_settings as agent
import llm
from corpus import DOCUMENTS
from routers.search_api import ENRICHED_DIR, _enrichment_files, _record
from project_backend import llm as observations_llm

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


# ENDPOINT 1 - all documents from the corpus (initial testing; may not be used in production)

@router.get("/documents")
def get_documents():
    """Get all documents from the corpus."""
    return DOCUMENTS


@router.get("/{case_id}")
def analyse_case_observations(case_id: str):
    """Return the original observations and overall assessment for a case."""
    rec = _record(case_id)
    document = next((item for item in DOCUMENTS if item["case_id"] == rec.case_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail=f"{case_id} not found")
    try:
        result = observations_llm.analyse_case(document)
        return {**result, "analysis_source": "anthropic", "reviewed_by_human": None}
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Summary provider timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Summary provider rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="Summary provider unavailable")
    except RuntimeError as exc:
        if "ANTHROPIC_API_KEY" not in str(exc):
            raise HTTPException(status_code=503, detail=str(exc))

        active_record, draft_record = _enrichment_files(rec.case_id)
        saved_record = active_record or draft_record
        if saved_record:
            observations = [
                saved_record.get("problem_plain"),
                saved_record.get("capability"),
                saved_record.get("scale_outcomes"),
            ]
            assessment = [saved_record.get("summary"), saved_record.get("reusable")]
            source = "saved_enrichment"
            reviewed = bool(saved_record.get("_agent", {}).get("reviewed_by_human", False))
        else:
            observations = re.split(r"(?<=[.!?。])\s+", rec.raw_text.strip())[:5]
            assessment = ["AI assessment unavailable until ANTHROPIC_API_KEY is configured."]
            source = "source_text"
            reviewed = None

        return {
            "analysis": {
                "Observations": [item for item in observations if item],
                "OverallAssesment": [item for item in assessment if item],
            },
            "input_tokens": 0,
            "output_tokens": 0,
            "stop_reason": "fallback",
            "analysis_source": source,
            "reviewed_by_human": reviewed,
        }


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
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ENDPOINT 3 - LLM ANALYSE ONE CASE by case_id (accepts case-209, 209, CASE-209, case-209.txt)

@router.post("/cases/{case_id}/analyse")
def analyse_case(case_id: str, save: bool = False):
    """Agent draft of the structured English record for one case.
    save=true writes it to the active enrichment folder and stores the untouched
    draft in the sibling enriched_draft folder; reindex afterwards to use it.
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
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if save:
        result["saved_to"] = str(llm.save_enrichment(
            result, rec.source_path, out_dir=ENRICHED_DIR))
    return result
