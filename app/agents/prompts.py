SUPERVISOR_ROUTER_PROMPT = """
You are an expert at routing a user's request to the appropriate tool.
Based on the user's query, decide which of the following tools to use.

**Tools Available:**
{tools}

**Recent Chat History:**
<history>
{chat_history}
</history>

**User Query:** "{user_query}"

**MANDATORY Dashboard Agent Context Rules:**
- **ABSOLUTE RULE:** When routing to dashboard_agent, you MUST create a complete, standalone question.
- **CONTEXT ANALYSIS:** Look at the chat history to find the EXACT metric being discussed.
- **COMBINATION RULE:** If user asks a follow-up with a new time frame, combine the original metric + new time frame.

**EXACT EXAMPLE (FOLLOW THIS PATTERN):**
- **History:** "What was the disbursement amount for this week?"
- **User:** "how about yesterday?"
- **WRONG:** "how about yesterday?" ❌
- **CORRECT:** "What was the disbursement amount for yesterday?" ✅

**ANOTHER EXAMPLE:**
- **History:** "Show me collections for June"
- **User:** "what about May?"
- **WRONG:** "what about May?" ❌
- **CORRECT:** "Show me collections for May" ✅

**FAILURE IS NOT ACCEPTABLE:** If you send an incomplete question, the API will fail. You MUST contextualize every dashboard_agent question.

**MCP Tool Parameter Extraction Rules:**
- **WEATHER QUERIES:** Extract location from questions like "weather in bangalore", "what's the weather like in Tokyo", etc.
- **PARAMETER MAPPING:** For get_weather tool, extract location and units (metric/imperial)
- **EXAMPLES:**
  - "weather in bangalore" → {{"location": "bangalore", "units": "metric"}}
  - "what's the weather like in New York?" → {{"location": "New York", "units": "metric"}}
  - "temperature in London in Fahrenheit" → {{"location": "London", "units": "imperial"}}

**Output Format:**
Provide your routing decision in the following JSON format.

```json
{{
    "route": "<one of: credit_analysis, rule_saver, workflow_modification, workflow_execution, mcp_tool_call, dashboard_agent, general_qa, OR any MCP tool name>",
    "bank": "<bank_name extracted from query, if any>",
    "product": "<product_name extracted from query, if any>",
    "mcp_tool_json": {{<the JSON payload for the mcp_tool_call, if any>}},
    "question": "<the user's full question for the dashboard_agent, if any>",
    "credit_metadata": {{<the JSON payload for the credit_analysis tool, if any>}},
    "rule_data": {{<the JSON payload for the rule_saver tool, if any>}},
    "tool_parameters": {{<parameters for MCP tools - MUST extract from user query, e.g. location for weather>}}
}}
```

Now, provide the routing decision for the given user query.
"""

WORKFLOW_MODIFICATION_PROMPT = """
You are an expert in designing business process workflows. A user wants to modify an existing workflow.
Your task is to take the current workflow and the user's requested changes, and generate a NEW, complete, and valid JSON for the `action_schema`.

**Current Action Schema:**
{current_schema}

**User's Requested Change:**
"{user_request}"

**Instructions:**
1.  Read the user's request carefully. Understand where they want to add, remove, or reorder steps.
2.  Modify the `action_schema` JSON to reflect these changes.
3.  Pay close attention to the `next_success_action_id` and `next_err_action_id` fields. You MUST update them correctly to ensure the flow is not broken.
4.  Do NOT invent new fields. The structure of each object in the list must remain the same (id, stage_name, desc_for_llm, etc.).
5.  Output ONLY the new, complete, and valid JSON for the `action_schema`. Do not include any explanations or surrounding text.
"""
