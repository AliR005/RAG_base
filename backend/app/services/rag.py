import yaml
from app.db.vector_store import VectorStore
from app.schemas.chat import Message
from app.services.history import format_history
from app.services.llm import LLMAssistant


def _load_template() -> str:
    with open("template.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["prompt"]


async def get_rag_answer(
    query: str,
    history: list[Message],
    db: VectorStore,
    llm: LLMAssistant,
) -> str:
    chat_history = ""
    if history:
        chat_history = format_history(history)

    _, context_chunks = db.find_relevant_context(
        db.model.encode(query), top_k=2
    )
    context = "\n\n[DOC]\n\n".join(context_chunks)

    prompt = _load_template().format(
        chat_history=chat_history,
        question=query,
        context=context,
    )

    return await llm.get_response(prompt)
