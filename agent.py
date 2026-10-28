"""The AI agent: Gemini + 2 tools (search the club info, hand off to a human)."""
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import knowledge

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

PROMPT_FILE = ROOT / "prompt.md"
# Main model first, then backups. Each has its own free-tier limit (about 5 requests per minute).
MODELS = [os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
          "gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
HISTORY_LIMIT = 16   # messages remembered per person
MAX_TOOL_CALLS = 3

FALLBACK_REPLY = ("Désolé, je rencontre un petit problème technique. Réessayez dans une minute.\n"
                  "عذراً، هناك مشكل تقني بسيط. حاول مرة أخرى بعد دقيقة.")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=30_000))
history: dict[str, list[tuple[str, str]]] = {}   # user id -> [(role, text), ...] (kept in memory)
_busy_until: dict[str, float] = {}               # model -> time when its rate limit should be over

TOOLS = [types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_knowledge",
        description="Search Smart Club's information (joining, events, formations, projects, team, contacts). "
                    "Write the query in French.",
        parameters_json_schema={"type": "object", "properties": {"query": {"type": "string"}},
                                "required": ["query"]},
    ),
    types.FunctionDeclaration(
        name="handoff_to_human",
        description="Pass the conversation to a human team member: sponsoring or partnership requests, "
                    "complaints, questions about someone's own application, someone asking for a person, "
                    "or anything you cannot answer from the search results.",
        parameters_json_schema={"type": "object", "properties": {"reason": {"type": "string"}},
                                "required": ["reason"]},
    ),
])]


def _search_text(query: str) -> str:
    results = knowledge.search(query)
    if not results:
        return "Nothing found."
    return "\n\n---\n\n".join(f"[{r['title']}]{' (' + r['url'] + ')' if r['url'] else ''}\n{r['text']}"
                              for r in results)


def _ask_gemini(model: str, contents: list) -> tuple[str, str | None]:
    """Runs the tool loop with one model. Returns (answer, handoff reason or None)."""
    contents = list(contents)
    handoff = None
    config = types.GenerateContentConfig(
        system_instruction=PROMPT_FILE.read_text(encoding="utf-8"),
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=types.ThinkingConfig(thinking_level="low"),  # short answers, faster
    )
    for _ in range(MAX_TOOL_CALLS + 1):
        response = client.models.generate_content(model=model, contents=contents, config=config)
        if not response.function_calls:
            return (response.text or "").strip(), handoff
        contents.append(response.candidates[0].content)
        results = []
        for call in response.function_calls:
            args = dict(call.args or {})
            print(f"  [tool] {call.name} {args}")
            if call.name == "search_knowledge":
                result = {"results": _search_text(args.get("query", ""))}
            else:
                handoff = args.get("reason", "")
                result = {"status": "done", "note": "Tell the person a team member will reply soon."}
            results.append(types.Part(function_response=types.FunctionResponse(
                id=call.id, name=call.name, response=result)))
        contents.append(types.Content(role="user", parts=results))
    return "", handoff


def reply(user_id: str, text: str) -> tuple[str, str | None]:
    """Answer one message. Returns (answer, handoff reason or None)."""
    past = history.setdefault(user_id, [])
    contents = [types.Content(role=role, parts=[types.Part(text=t)]) for role, t in past]
    # Search before asking Gemini, so most messages need a single Gemini call.
    found = _search_text(text)
    contents.append(types.Content(role="user", parts=[
        types.Part(text=text),
        types.Part(text="Search results already found for this message (use them; call search_knowledge "
                        "only if something is missing):\n\n" + found),
    ]))

    answer, handoff = "", None
    for model in [m for m in MODELS if _busy_until.get(m, 0) < time.time()] or MODELS[:1]:
        try:
            answer, handoff = _ask_gemini(model, contents)
            break
        except errors.APIError as e:
            if e.code == 429:
                _busy_until[model] = time.time() + 60   # skip this model for a minute
            print(f"  [agent] {model} unavailable ({e.code}), trying the next one")
        except httpx.TimeoutException:
            print(f"  [agent] {model} timed out, trying the next one")

    answer = answer or FALLBACK_REPLY
    past += [("user", text), ("model", answer)]
    del past[:-HISTORY_LIMIT]
    return answer, handoff
