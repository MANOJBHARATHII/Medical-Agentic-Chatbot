from groq.types.chat import ChatCompletionContentPartImageParam, ChatCompletionContentPartTextParam

from app.config import settings
from app.knowledge import client, search_kb


MEDICAL_ASSISTANT_PROMPT = (
    "You are a medical information assistant. Give clear, cautious, general health information, "
    "not a diagnosis or a substitute for a qualified clinician. Encourage users to seek medical "
    "care for personal medical decisions. If symptoms may indicate an emergency, tell the user "
    "to contact local emergency services immediately. Do not claim certainty from an image."
)


def respond(messages, image_url=None, use_knowledge=True):
    groq_client = client()[1]
    latest_question = next(
        (message["content"] for message in reversed(messages) if message["role"] == "user"),
        None,
    )
    if latest_question is None:
        raise ValueError("At least one user message is required.")

    system_prompt = MEDICAL_ASSISTANT_PROMPT
    if use_knowledge:
        passages = search_kb(latest_question)
        if passages:
            context = "\n\n".join(
                f"Page {passage['page']}: {passage['text']}" for passage in passages
            )
            system_prompt += (
                "\n\nUse the following retrieved reference passages when relevant. "
                "They are informational context and may be incomplete:\n" + context
            )

    request_messages = [{"role": "system", "content": system_prompt}, *messages]
    if image_url:
        latest_user_index = max(
            index for index, message in enumerate(request_messages)
            if message["role"] == "user"
        )
        request_messages[latest_user_index] = {
            "role": "user",
            "content": [
                ChatCompletionContentPartTextParam(
                    type="text",
                    text=request_messages[latest_user_index]["content"],
                ),
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={"url": image_url},
                ),
            ],
        }

    completion = groq_client.chat.completions.create(
        model=settings.vision_model if image_url else settings.chat_model,
        messages=request_messages,
        temperature=0.3,
    )
    answer = completion.choices[0].message.content
    if not answer:
        raise RuntimeError("Groq returned an empty response.")
    return answer