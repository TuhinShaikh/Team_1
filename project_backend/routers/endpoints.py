




from fastapi import APIRouter, HTTPException
from corpus import DOCUMENTS



router = APIRouter(prefix = "/endpoints", tags=["endpoints"])



#ENDPOINT 1 - Getting all documents from the corpus (inital testing purpose,might not be used in production)


@router.get("/documents")
def get_documents():
    """
    Get all documents from the corpus.
    """
    return DOCUMENTS

   
#ENDPOINT 2







#ENDPOINT 1 

