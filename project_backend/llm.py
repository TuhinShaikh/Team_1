




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

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Create the Anthropic client only when an AI feature is requested."""
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for AI features.")
        _client = anthropic.Anthropic(
            api_key=api_key,
            timeout=30.0,
            max_retries=3,
        )
    return _client


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
        "Analyse this sales case in a concise, comprehensive manner. "
        "Base every observation and assessment only on the supplied case text. "
        f"Case title: {fund_factsheet.get('delivery', 'Not provided')}\n"
        f"Case ID: {fund_factsheet.get('case_id', 'Not provided')}\n"
        f"Body: {fund_factsheet.get('body', '')}"
    )

#



class CaseAnalysis(BaseModel):
    """validation- The shape we require back,it is not suggestion to model ,it is a contract""" 
    Observations: list[str] = Field(max_length=5)
    OverallAssesment: list[str] = Field(max_length=3)


def analyse_case(case: dict) -> dict:
    """Structured output. The response is validated against the FirmAnalsyis... or it fails """
    response = get_client().messages.parse(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(case)}],
        output_format= CaseAnalysis, 
    )

    #not free text returned ?based on schema 
    analysis = response.content[0].parsed_output

    return {
        "analysis": analysis,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }
