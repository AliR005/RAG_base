# services/history.py
from app.schemas.chat import Message


def format_history(history: list[Message]) -> str:
    if not history:
        return ""

    lines = ["История чата:"]
    for msg in history:
        prefix = "Вопрос" if msg.role == "user" else "Ответ"
        lines.append(f"{prefix}: {msg.content}")

    return "\n".join(lines) + "\n"
