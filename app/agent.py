import json
from typing import Any, TypedDict

from groq.types.chat import ChatCompletionContentPartImageParam, ChatCompletionContentPartTextParam
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.knowledge import client, search_kb


MEDICAL_ASSISTANT_PROMPT = (
    "You are a medical information assistant. Give clear, cautious, general health information, "
    "not a diagnosis or a substitute for a qualified clinician. Encourage users to seek medical "
    "care for personal medical decisions. If symptoms may indicate an emergency, tell the user "
    "to contact local emergency services immediately. Do not claim certainty from an image."
)

PLANNER_PROMPT = (
    "Decide whether the user's latest medical-information question could benefit from searching "
    "a medical reference book. Greetings, general conversation, and questions unrelated to medical "
    "reference material do not need retrieval. Return only a JSON object with exactly these keys: "
    '{"needs_retrieval": boolean, "search_query": string}. If retrieval is not needed, use an empty '
    "search_query. If it is needed, provide a short focused search query without adding facts."
)


class AgentState(TypedDict, total=False):
    messages: list[dict[str, Any]]
    image_url: str | None
    use_knowledge: bool
    question: str
    should_retrieve: bool
    search_query: str
    passages: list[dict[str, Any]]
    answer: str


def _latest_user_message(messages: list[dict[str, Any]]) -> dict[str, Any]:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message
    raise ValueError("At least one user message is required.")


def _text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def _prepare_request(state: AgentState) -> dict[str, Any]:
    message = _latest_user_message(state["messages"])
    question = _text_content(message.get("content", "")).strip()
    if not question:
        raise ValueError("The latest user message must contain text.")
    return {"question": question}


def _plan_retrieval(state: AgentState) -> dict[str, Any]:
    if not state.get("use_knowledge", True):
        return {"should_retrieve": False, "search_query": ""}

    groq_client = client()[1]
    response = groq_client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": state["question"]},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty retrieval plan.")
    try:
        plan = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Groq returned an invalid retrieval plan.") from exc

    should_retrieve = plan.get("needs_retrieval")
    search_query = plan.get("search_query")
    if not isinstance(should_retrieve, bool) or not isinstance(search_query, str):
        raise RuntimeError("Groq returned a retrieval plan with an invalid shape.")
    return {
        "should_retrieve": should_retrieve and bool(search_query.strip()),
        "search_query": search_query.strip(),
    }


def _route_after_planning(state: AgentState) -> str:
    return "retrieve" if state.get("should_retrieve", False) else "answer"


def _retrieve_context(state: AgentState) -> dict[str, Any]:
    return {"passages": search_kb(state["search_query"])}


def _generate_answer(state: AgentState) -> dict[str, str]:
    system_prompt = MEDICAL_ASSISTANT_PROMPT
    passages = state.get("passages", [])
    if passages:
        context = "\n\n".join(
            f"Page {passage['page']}: {passage['text']}" for passage in passages
        )
        system_prompt += (
            "\n\nUse the following retrieved reference passages when relevant. Cite the page "
            "number when using them. They are informational context and may be incomplete:\n"
            + context
        )

    request_messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *state["messages"],
    ]
    image_url = state.get("image_url")
    if image_url:
        latest_user_index = max(
            index for index, message in enumerate(request_messages)
            if message["role"] == "user"
        )
        user_content = _text_content(request_messages[latest_user_index]["content"])
        request_messages[latest_user_index] = {
            "role": "user",
            "content": [
                ChatCompletionContentPartTextParam(type="text", text=user_content),
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={"url": image_url},
                ),
            ],
        }

    groq_client = client()[1]
    completion = groq_client.chat.completions.create(
        model=settings.vision_model if image_url else settings.chat_model,
        messages=request_messages,
        temperature=0.3,
    )
    answer = completion.choices[0].message.content
    if not answer:
        raise RuntimeError("Groq returned an empty response.")
    return {"answer": answer}


def _build_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("prepare_request", _prepare_request)
    workflow.add_node("plan_retrieval", _plan_retrieval)
    workflow.add_node("retrieve_context", _retrieve_context)
    workflow.add_node("generate_answer", _generate_answer)

    workflow.add_edge(START, "prepare_request")
    workflow.add_edge("prepare_request", "plan_retrieval")
    workflow.add_conditional_edges(
        "plan_retrieval",
        _route_after_planning,
        {"retrieve": "retrieve_context", "answer": "generate_answer"},
    )
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", END)
    return workflow.compile()


agent_workflow = _build_workflow()


def respond(messages, image_url=None, use_knowledge=True):
    result = agent_workflow.invoke(
        {
            "messages": messages,
            "image_url": image_url,
            "use_knowledge": use_knowledge,
        }
    )
    return result["answer"]
