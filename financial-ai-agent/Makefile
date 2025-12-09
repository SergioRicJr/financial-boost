# Financial AI Agent - Makefile
# ================================

.PHONY: help install dev run test lint format docker-up docker-down clean seed

# Cores para output
GREEN := \033[0;32m
NC := \033[0m

help: ## Mostra esta ajuda
	@echo "Financial AI Agent - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências
	pip install -r requirements.txt

dev: ## Instala dependências de desenvolvimento
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black ruff mypy

run: ## Executa a aplicação
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Executa em modo produção
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Executa testes
	pytest -v

test-cov: ## Executa testes com cobertura
	pytest --cov=app --cov-report=html --cov-report=term

lint: ## Executa linting
	ruff check app tests
	mypy app

format: ## Formata o código
	black app tests
	ruff check --fix app tests

docker-up: ## Sobe containers Docker
	docker-compose up -d

docker-down: ## Para containers Docker
	docker-compose down

docker-logs: ## Mostra logs dos containers
	docker-compose logs -f

docker-build: ## Rebuild dos containers
	docker-compose build --no-cache

seed: ## Popula banco com dados de exemplo
	python scripts/seed_data.py

clean: ## Limpa arquivos temporários
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage
	rm -f test.db

init-db: ## Inicializa o banco de dados
	python -c "import asyncio; from app.db.database import init_db; asyncio.run(init_db())"

shell: ## Abre shell Python com contexto da aplicação
	python -c "from app.core.config import settings; print('Settings loaded'); import IPython; IPython.embed()" || python -i -c "from app.core.config import settings; print('Settings loaded')"
