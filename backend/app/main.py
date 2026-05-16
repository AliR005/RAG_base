import uvicorn
import yaml
from chat.chat_history import append_history
from config import Settings
from fastapi import FastAPI
from llm import LLMAssistant
from vector_store import VectorStore

app = FastAPI()
db = VectorStore()
settings = Settings()
llm = LLMAssistant()

try:
    with open("template.yaml", "r", encoding="utf-8") as file:
        prompt_template: str = yaml.safe_load(file)["prompt"]
except FileNotFoundError:
    raise RuntimeError("Не найден файл template.yaml")
except yaml.YAMLError as e:
    raise RuntimeError(f"Ошибка в template.yaml: {e}")


@app.post("/query/")
async def query(data: dict):
    question = data.get("query", "")
    history = data.get("history", [])

    chat_history = ""
    if history:
        chat_history = append_history(history=history)

    _, context_chunks = db.find_relevant_context(
        db.model.encode(question), top_k=4
    )
    context = "\n---\n".join(context_chunks)

    prompt = prompt_template.format(
        chat_history=chat_history, question=question, context=context
    )
    result = await llm.get_response(prompt)

    return {"answer": result}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host=settings.HOST, port=settings.PORT)
