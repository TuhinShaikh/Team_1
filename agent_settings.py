

""" 
This is the place agent+tool use loop  will be initilised. 
It allows agent to use two tools: 
>search with agent (knowledge/ask )

"""

from routers.search_api import index as search_index
from llm import MODEL,client


# agent system prompt 

AGENT_SYSTEM_PROMPT = (
    "You are Sales Support Assistent with access to tools to a search tool over cases"
    "knowledge base. Use the tool whenever a question needs "
    "information  you don't already have  - do not guess. Cite document ids in "
    "your final answer. If the tool returns nothing relevent,say so honestly. "
)



# TOOL 1 - search tool 

SEARCH_TOOL = {
    "name": "search_knowledge_base",
    "description": (
        "Search the cases knowledge base for documents relevent "
        "to the question. Return a list of document ids and their content. "
    ),
    "input_schema": {
        "type":"object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required":["query"], 
    },  

}




#the loop , we call, check and maybe repeat
MAX_ITERATIONS = 4   #at least 4 times loop runs 
def ask_with_tools(question:str) -> dict:
    """ Run the tool use loop until model answers or the limit is hit"""
    messages = [{"role":"user", "content": question}]
    total_input_tokens = 0 
    total_output_tokens = 0 
    tool_calls_made = 0 

    #the loop 
    for _ in range(MAX_ITERATIONS):
        response = client.messages.create(
                    model=MODEL,
                    max_tokens=600,
                    system=AGENT_SYSTEM_PROMPT,
                    tools=[SEARCH_TOOL], 
                    messages=messages,
                )
        
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # checking wheter the model is done
        if response.stop_reason != "tool_use":
            final_text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )

            return {
                "answer":final_text,
                "completed":True,
                "tool_calls_made": tool_calls_made,
                "input_tokens": total_input_tokens, 
                "output_tokens": total_output_tokens,
                "stop_reason":response.stop_reason,
            }

        #models request - has name, id etc 
        # response  content - when added to messages per round 
        tool_blocks = [b for b in response.content if b.type =="tool_use"]
        messages.append({"role":"assistant", "content": response.content})

        tool_results = [] 
        for tool_block in tool_blocks:
            result_text , is_error = _execute_tool(tool_block.name, tool_block.input)
            if not is_error:
                tool_calls_made += 1

            tool_results.append ({
                "type": "tool_result",
                "tool_use_id": tool_block.id, 
                "content": result_text,
                "is_error": is_error
            })

        
        #expect in tool use(model side) +tool result (query side)
        messages.append({"role":"user", "content": tool_results})

    return {
        "answer": "Reached maximum iterations without a final response.",
        "completed": False,
        "tool_calls_made": tool_calls_made,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "stop_reason": "max_iterations",
    }




def _execute_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run the requested tool. Returns (result_text, is_error)."""
    # Guard 1: only one valid tool
    if name != "search_knowledge_base":
        return f"Unknown tool: {name}", True

    # Guard 2: required argument
    query = (tool_input.get("query") or "").strip()
    if len(query) < 3:
        return "Error: missing or too-short field: query", True

    out = search_index().search(query, k=3)
    if out["no_strong_match"]:
        return "No strong match in the case corpus. Say so honestly; do not guess.", False

    records = {r.case_id: r for r in search_index().records}
    formatted = "\n\n".join(
        f"[{r['case_id']}] (similarity {r['similarity']})\n"
        f"Why it matched: {r['why']}\n"
        f"Source text: {records[r['case_id']].raw_text}"
        for r in out["results"] if r["strong_match"]
    )
    return formatted, False

        

    # The real success path - geniune results , formatted for the model to read. 
    formatted = "\n\n".join(
            f"[{r['id']}] {r['title']} (score {r['score']:.2f})\n{r['Content']}"
            for r in results
    )
    return formatted, False