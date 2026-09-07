# 🚀 RAG System (Retrieval-Augmented Generation)

Production-ready система для работы с документами с использованием RAG.

Позволяет загружать любые данные (пока только из DOCX), находить релевантный контекст и генерировать ответы с помощью LLM.

---

## ✨ Возможности

- 📄 Загрузка документов (DOCX)
- 🧠 Генерация embeddings
- 🔍 Семантический поиск (vector search)
- 🤖 Ответы через LLM (Ollama)
- ⚡ Быстрый и расширяемый pipeline

---

## 🧱 Архитектура

Documents → Chunking → Embeddings → Vector DB → Retrieval → LLM → Answer

---

## 🛠 Стек технологий

- Python
- ChromaDB
- SentenceTransformers
- FastAPI
- Streamlit
- Ollama
- uv

---

## 📦 Установка

```bash
git clone <repo>
cd <project>

uv init
uv add -r requirements.txt
```

---

## 📄 Подготовка данных
В `/backend/docs` должны находиться данные формата .docx,
которые будут использоваться для внесения в бд.


## 🧠 Загрузка документов

```bash
uv run load_docs.py
```

Что происходит:
- документы разбиваются на чанки
- создаются embeddings
- данные сохраняются в ChromaDB

---

## ⚙️ Настройка

Создай `.env` и заполинте по примеру из `.env_example`


---

## 🚀 Запуск проекта
  1. make
  1. make model_up (для остановки 'make model_down')
  2. ctrl+d или создать новую сессию в терминале
  3. make run (для остановки 'make stop)
  4. открыть страниу по одному из предложенний адресов (например, 'http://localhost:8502')

---

## 💡 Как это работает

1. Запрос → embedding  
2. Поиск похожих чанков  
3. Передача контекста в LLM  
4. Генерация ответа 

---

## 📈 Возможные улучшения

- Reranker (улучшение поиска)
- Metadata filtering
- Более мощные embedding модели
- Docker / деплой

---

## 👨‍💻 Описание

Проект демонстрирует полный pipeline RAG-системы:
от загрузки документов до генерации ответов.

Подходит для:
- knowledge base
- чат-ботов
- поиска по документации
- корпоративных ассистентов
