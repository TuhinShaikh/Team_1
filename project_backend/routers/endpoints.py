




from fastapi import APIRouter, HTTPException
from corpus import DOCUMENTS
import agent_settings as agent 
from pydantic import BaseModel

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








#ENDPOINT 1 

