.PHONY: help docs backend frontend run stop clean model_up model_down

include .env
export

help:
	@echo "Доступные команды:"
	@echo "  make docs        - загрузка документов в ChromaDB"
	@echo "  make model_up    - запуск Ollama модели"
	@echo "  make model_down  - остановка Ollama модели"
	@echo "  make backend     - запуск FastAPI backend"
	@echo "  make frontend    - запуск Streamlit frontend"
	@echo "  make run         - запуск backend + frontend"
	@echo "  make stop        - остановка backend + frontend"

docs:
	cd backend && uv run python -m app.scripts.load_docs

model_up:
	ollama run $(LLM_MODEL) &

model_down:
	ollama stop $(LLM_MODEL)

backend:
	cd backend && uv run uvicorn app.main:app --host $(HOST) --port $(PORT)

frontend:
	cd frontend && uv run streamlit run ui.py

run:
	$(MAKE) -j2 backend frontend &
	@echo ""
	@echo "Backend:  http://$(HOST):$(PORT)"
	@echo "Frontend: http://localhost:8501"

stop:
	@pkill -f uvicorn || true
	@pkill -f streamlit || true
	@echo "Остановлено"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .chroma -exec rm -rf {} + 2>/dev/null || true
