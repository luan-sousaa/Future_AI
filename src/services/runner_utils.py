from google.genai.types import Part


def extract_user_visible_text(parts: list[Part]) -> str:
    visible_chunks: list[str] = []

    for part in parts:
        if getattr(part, "thought", False):
            continue
        if part.text:
            visible_chunks.append(part.text.strip())

    return "\n".join(chunk for chunk in visible_chunks if chunk).strip()
