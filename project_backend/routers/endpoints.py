




from fastapi import APIRouter, HTTPException,Depends 
from corpus import DOCUMENTS
import agent_settings as agent 
from pydantic import BaseModel

import llm 

router = APIRouter(prefix = "/endpoints", tags=["endpoints"])



#ENDPOINT 1 - Getting all documents from the corpus (inital testing purpose,might not be used in production)


@router.get("/documents")
def get_documents():
    """
    Get all documents from the corpus.
    """
    return DOCUMENTS



from anthropic import APIStatusError, APITimeoutError, RateLimitError

#ENDPOINT 2 - AGENT_ASK 
class AskRequest(BaseModel):
    question: str

@router.post("/ask")
def ask(req: AskRequest):
    try:
        result = agent.ask_with_tools(req.question)
        return result
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI Agent timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="AI Agent rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="AI Agent unavailable")





#ENDPOINT 3 - LLM ANALYSE SPECIFIC DOCUMENT BY case_id ( like case-209)


#this is helper function to search for the case 
def get_case_or_404(case_id: str) -> dict:
    for document in DOCUMENTS:
        if document["case_id"] == case_id:
            return document["body"]
    raise HTTPException(status_code=404, detail=f"No case with id {case_id}")

@router.get("/{case_id}")
def analyse_case(case: dict = Depends(get_case_or_404)):
    try:
        return llm.analyse_case(case)
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Summary provider timed out")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Summary provider rate limited")
    except APIStatusError:
        raise HTTPException(status_code=502, detail="Summary provider unavailable")
