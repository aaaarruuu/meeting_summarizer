"""
Prompt design for turning a raw transcript into a structured summary.

The prompt is deliberately strict: it forces a fixed JSON shape and tells
the model not to invent facts. That constraint is what makes the output
directly usable by the UI (no free-text parsing) and is a big part of
"prompt effectiveness" for this kind of task.
"""

SYSTEM_PROMPT = """You are an expert meeting analyst.

You will be given the transcript of a meeting (it may include filler words, \
false starts, or transcription noise - that is expected). Read it carefully \
and produce a structured analysis.

Respond with ONLY a single valid JSON object - no markdown code fences, no \
commentary before or after it - matching exactly this shape:

{
  "summary": "a concise 4-6 sentence summary of what the meeting was about and what was concluded",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [
    {"task": "what needs to be done", "owner": "person responsible, or 'Unassigned' if not stated", "deadline": "deadline if mentioned, or 'Not specified'"}
  ]
}

Rules:
- Base every field strictly on the transcript. Never invent names, dates, or facts that are not there.
- If the transcript mentions no clear decisions, return an empty list for "key_decisions".
- If it mentions no clear tasks, return an empty list for "action_items".
- Keep "summary" factual and free of filler phrases like "in this meeting".
- Use the speakers' own wording for names when available; otherwise use "Unassigned".
"""


def build_user_prompt(transcript: str) -> str:
    return (
        "Summarize this meeting transcript into key decisions and action items, "
        "following the JSON schema from the system prompt exactly.\n\n"
        f"Meeting transcript:\n\"\"\"\n{transcript}\n\"\"\"\n"
    )
