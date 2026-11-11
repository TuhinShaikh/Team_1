




#how we call the model (nothing knows about fastapi )

#api burnt at end of day 
#dont close (set on session)

import os
import anthropic

from anthropic import APIStatusError, APITimeoutError,RateLimitError

from pydantic import BaseModel, Field


#Not needed right now (not implemented)
# import time
#import grounding 

MODEL = "claude-haiku-4-5-20251001"

#the sdk defualt are max retry 2 ,600 second timeout
#overwritten here as descision

client = anthropic.Anthropic(
    api_key = os.environ["ANTHROPIC_API_KEY"],
    timeout=30.0,
    max_retries=3,

)


#the prompt and where the rules live 

#RULES GO IN SYSTEM
#DATA GOES IN USER 

#-----------------------LLM s---------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a helpfull . "
    "Use British English "
     
)


#this function is too build the prompt used to summarise fund fact sheets by fund id 
def build_prompt( fund_factsheet:dict) -> str:
    return (
        f"Summarise this investment fund factsheet for a portfolio manager in formal yet fun way"
        f"Name: {fund_factsheet["title"]} "
        f"Body:{fund_factsheet["body"]} "
    )

#




