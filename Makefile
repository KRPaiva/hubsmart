.PHONY: help setup dev test test-unit lint format migrate seed check-stack clean

SHELL := /bin/bash

help: ## Exibe os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Instala dependências e aplica migrations no SQLite local
	@if [ ! -f .env ]; then cp .env.example .env; fi
	poetry install --with dev
	poetry run alembic upgrade head

dev: ## Inicia o FastAPI local em http://localhost:8000
	poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Aplica migrations
	poetry run alembic upgrade head

seed: ## Cria usuário demo, workspace e flashcards de exemplo
	poetry run python -m scripts.seed_dev

test: ## Executa todos os testes no SQLite de teste
	poetry run pytest

test-unit: ## Executa apenas testes unitários sem banco
	poetry run pytest tests/test_spaced_repetition.py

lint: ## Verifica stack e estilo
	./scripts/check_no_node.sh
	poetry run ruff check app tests scripts
	poetry run ruff format --check app tests scripts

format: ## Formata código com Ruff
	poetry run ruff check --fix app tests scripts
	poetry run ruff format app tests scripts

check-stack: ## Verifica política Zero Node/NPM
	./scripts/check_no_node.sh

clean: ## Remove caches locais
	rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
	rm -f hubsmart_brainstorm.db hubsmart_brainstorm_test.db hubsmart_brainstorm.db-shm hubsmart_brainstorm.db-wal hubsmart_brainstorm_test.db-shm hubsmart_brainstorm_test.db-wal
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
