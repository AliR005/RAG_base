.PHONY: help docs backend frontend model run stop clean

include .env
export

BACKEND_PID=.backend.pid
FRONTEND_PID=.frontend.pid

help:
	@echo "Доступные команды:"
	@echo " make docs       - загрузка документов в ChromaDB"
	@echo " make model_up   - запуск Ollama модели"
	@echo " make model_down - остановка Ollama модели"
	@echo " make backend    - запуск FastAPI backend"
	@echo " make frontend   - запуск Streamlit frontend"
	@echo " make run        - запуск backend + frontend"
	@echo " make stop       - остановка backend + frontend"

docs:
	uv run load_docs.py

model_up:
	ollama run $(MODELNAME) &

model_down:
	ollama stop $(MODELNAME)

backend:
	cd backend/app && \
	uv run main.py & \
	echo $$! > ../../$(BACKEND_PID)
	@echo "Backend started"

frontend:
	cd frontend && \
	streamlit run ui.py & \
	echo $$! > ../$(FRONTEND_PID)
	@echo "Frontend started"

run:
	$(MAKE) backend
	$(MAKE) frontend
	@echo ""
	@echo "Backend:  http://localhost:$(PORT)"
	@echo "Frontend: http://localhost:8501"

stop:
	@if [ -f $(BACKEND_PID) ]; then \
		kill `cat $(BACKEND_PID)` && rm $(BACKEND_PID); \
		echo "Backend stopped"; \
	fi

	@if [ -f $(FRONTEND_PID) ]; then \
		kill `cat $(FRONTEND_PID)` && rm $(FRONTEND_PID); \
		echo "Frontend stopped"; \
	fi

clean:
	rm -f $(BACKEND_PID) $(FRONTEND_PID)
