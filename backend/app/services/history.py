# services/history.py
from app.domain.chat import ChatMessage


def format_history(history: list[ChatMessage]) -> str:
    if not history:
        return ""

    lines = ["История чата:"]
    for msg in history:
        prefix = "Вопрос" if msg.role == "user" else "Ответ"
        lines.append(f"{prefix}: {msg.content}")

    return "\n".join(lines) + "\n"
