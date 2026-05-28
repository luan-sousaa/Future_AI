import re

THINKING_BLOCK_PATTERN = re.compile(
    r"<think>.*?</think>",
    re.DOTALL | re.IGNORECASE,
)

def hide_reasoning_callback(callback_context, llm_response):
    if not llm_response.content:
        return None

    changed = False

    for part in llm_response.content.parts:
        if not getattr(part, "text", None):
            continue

        sanitized = THINKING_BLOCK_PATTERN.sub("", part.text)

        if sanitized != part.text:
            part.text = sanitized.strip()
            changed = True

    return llm_response if changed else None