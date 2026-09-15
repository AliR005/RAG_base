# 🚀 RAG System (Retrieval-Augmented Generation)

RAG-система для работы с документами: загрузка DOCX, семантический поиск
и генерация ответов через LLM. Учебный проект, доводится до уровня
портфолио AI Engineer (см. `AGENTS.md`).

---

## ✨ Возможности

- 📄 Загрузка документов (DOCX, сплит по маркеру `##`, таблицы в markdown)
- 🧠 Эмбеддинги (`intfloat/multilingual-e5-base`, меняется через `.env`)
- 🔍 Семантический поиск (ChromaDB)
- 🤖 Ответы через LLM (Ollama)
- 💬 Чат-интерфейс (Streamlit)

---

## 🧱 Архитектура

```
Documents → Chunking → Embeddings → Vector DB → Retrieval → LLM → Answer
```

- `backend/app` — FastAPI-бэкенд (`main.py`, `routers/`, `services/`, `db/`)
- `backend/app/domain|ports|application|adapters|api` — скелет чистой
  архитектуры (заполняется по roadmap в `AGENTS.md`)
- `backend/tests` — тесты (`pytest`)
- `frontend/` — Streamlit-интерфейс (`ui.py`)

---

## 🛠 Стек технологий

Python 3.14 · FastAPI · ChromaDB · SentenceTransformers · Ollama ·
Streamlit · uv · ruff · pre-commit · pytest

---

## 📦 Установка

```bash
git clone git@github.com:AliR005/RAG_base.git
cd RAG_base

cp .env_example .env   # заполнить LLM_MODEL и остальное
uv sync --group dev
```

Для git-хуков (ruff + ruff-format):

```bash
uv run pre-commit install
```

---

## ⚙️ Настройка

Переменные окружения (все значения по умолчанию — в
`backend/app/core/config.py`):

| Переменная | Назначение |
|---|---|
| `HOST`, `PORT` | адрес и порт FastAPI |
| `LLM_MODEL` | модель Ollama |
| `EMBEDDING_MODEL` | модель эмбеддингов |
| `COLLECTION_NAME` | коллекция ChromaDB |

---

## 📄 Загрузка документов

Положить `.docx`-файлы в `backend/docs/` (чанки режутся по маркеру `##`
в тексте; документы без `##` пропускаются), затем:

```bash
make docs
```

---

## 🚀 Запуск проекта

```bash
make model_up   # запуск модели Ollama (остановка: make model_down)
make run        # backend + frontend (остановка: make stop)
```

- Backend: `http://$HOST:$PORT` (по умолчанию `http://0.0.0.0:8000`)
- Frontend: `http://localhost:8501`
- Проверка: `GET /health`

Отдельно: `make backend`, `make frontend`.

---

## 🧹 Разработка

```bash
uv run ruff check backend frontend
uv run ruff format --check backend frontend
uv run pytest
```

---

## 💡 Как это работает

1. Запрос → embedding
2. Поиск похожих чанков (`top_k=2`)
3. Подстановка контекста и истории в промпт (`backend/template.yaml`)
4. Генерация ответа через Ollama

---

## 📈 Дальше по плану

Полный roadmap — в `AGENTS.md` (раздел 8): доменные сущности и порты,
Qdrant + гибридный поиск, реранкинг, провайдеры LLM, SSE-стриминг, auth,
Postgres, Next.js-фронтенд, CI, Docker.
