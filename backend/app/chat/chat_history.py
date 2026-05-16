from typing import Dict, List


def append_history(history: List[Dict[str, str]]) -> str:
    chat_history = ""
    try:
        chat_history = "История чата:\n"
        for msg in history:
            if msg["role"] == "user":
                chat_history += f"Вопрос: {msg['content']}\n"
            else:
                chat_history += f"Ответ: {msg['content']}\n"
        chat_history += "\n"
    except Exception as e:
        chat_history = f"Chat history error: {str(e)}"

    return chat_history
