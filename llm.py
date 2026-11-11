"""How we call the model. Nothing here knows about FastAPI.

analyse_case() turns one raw case into a structured English record that
matches the search's enrichment fields. Save it with save_enrichment() and
search.py picks it up from data/enriched/ on the next /api/reindex.

Every record is an agent DRAFT: a person must check it against the source
before it counts as reviewed (brief: spot-check at least 10, keep both).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-haiku-4-5-20251001"

# SDK defaults are 2 retries and a 600 s timeout; overridden here as a decision.
# getenv (not environ[...]) so the server still starts without a key and only
# the LLM features fail.
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=30.0,
    max_retries=3,
)

# Rules go in the system prompt; data goes in the user message.
SYSTEM_PROMPT = (
    "You analyse past delivery case studies for sales and delivery leads. "
    "Use only facts stated in the case text. Never add figures, clients, dates or "
    "outcomes that are not in the text. Copy every number exactly as written. "
    "If the case text is not in English, write every field in English. "
    "If something is not stated, write 'Not stated' rather than guessing. "
    "Use British English."
)


class CaseAnalysis(BaseModel):
    """The shape we require back. It is a contract, not a suggestion."""
    language: str = Field(description="Language the source text is written in, e.g. 'German'")
    sector: str = Field(description="Client's industry, e.g. 'Insurance'")
    country: str = Field(description="Country or region of the client, or 'Not stated'")
    problem_plain: str = Field(description="The client's problem in one or two plain-English sentences")
    capability: str = Field(description="What was done: technique, technology or approach")
    scale_outcomes: str = Field(description="Scale and outcome figures, copied exactly from the text")
    reusable: str = Field(description="What could be reused for another client")
    summary: str = Field(description="Two sentences in English, only claims stated in the text")


# Forcing a single tool call is how we get schema-shaped output that works on
# any recent SDK version; the result is then validated by Pydantic.
ENRICH_TOOL = {
    "name": "record_case_analysis",
    "description": "Record the structured analysis of one delivery case.",
    "input_schema": CaseAnalysis.model_json_schema(),
}


def build_prompt(case_id: str, text: str) -> str:
    return (
        "Analyse this past delivery case. Use only the text below.\n\n"
        f"Case ID: {case_id}\n"
        f"Text:\n{text}"
    )


def analyse_case(case_id: str, text: str) -> dict:
    """Structured output, validated against CaseAnalysis, or it raises."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        tools=[ENRICH_TOOL],
        tool_choice={"type": "tool", "name": ENRICH_TOOL["name"]},
        messages=[{"role": "user", "content": build_prompt(case_id, text)}],
    )
    block = next(b for b in response.content if b.type == "tool_use")
    analysis = CaseAnalysis.model_validate(block.input)

    return {
        "case_id": case_id,
        "analysis": analysis.model_dump(),
        "model": MODEL,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


def save_enrichment(result: dict, source_path: str, out_dir: str = "data/enriched") -> Path:
    """Write the record in the shape search.py reads (one JSON per case).
    Also keeps an untouched copy in data/enriched_draft/ so the human-corrected
    version can be shown side by side with the agent's draft."""
    record = {"case_id": result["case_id"], "source_path": source_path,
              **result["analysis"],
              "_agent": {"model": result["model"],
                         "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "reviewed_by_human": False}}
    for folder in (out_dir, "data/enriched_draft"):
        Path(folder).mkdir(parents=True, exist_ok=True)
        path = Path(folder) / f"{result['case_id']}.json"
        if folder == out_dir and path.exists():
            continue  # never overwrite a record a person may already have corrected
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return Path(out_dir) / f"{result['case_id']}.json"


if __name__ == "__main__":
    # python llm.py data/corpus/case-714.txt   -> analyse one case and save it
    import sys
    for arg in sys.argv[1:]:
        p = Path(arg)
        out = analyse_case(p.stem, p.read_text(encoding="utf-8"))
        print(json.dumps(out["analysis"], indent=2, ensure_ascii=False))
        print(f"saved -> {save_enrichment(out, str(p))}")