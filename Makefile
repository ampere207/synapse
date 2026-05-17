# Makefile for common development tasks
.PHONY: help install dev dev-backend dev-frontend up down logs clean test lint worker

help:
	@echo "Synapse - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services (Docker)"
	@echo "  make dev-backend    - Start backend only"
	@echo "  make dev-frontend   - Start frontend only"
	@echo ""
	@echo "Docker:"
	@echo "  make up             - Start Docker Compose"
	@echo "  make down           - Stop Docker Compose"
	@echo "  make logs           - View Docker logs"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make build          - Rebuild Docker images"
	@echo "  make worker         - Start AI worker service"
	@echo ""
	@echo "Maintenance:"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting"
	@echo ""

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	@echo "✓ Dependencies installed"

dev:
	docker-compose up

dev-backend:
	cd backend && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

up:
	docker-compose up -d
	@echo "✓ Services started"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
	@echo "Docs:     http://localhost:8000/docs"

down:
	docker-compose down
	@echo "✓ Services stopped"

logs:
	docker-compose logs -f

build:
	docker-compose build --no-cache

clean:
	docker-compose down -v
	@echo "✓ Containers and volumes removed"

worker:
	docker-compose up -d --profile workers ai_worker
	@echo "✓ AI worker started"

test:
	@echo "Running tests..."
	cd backend && pytest
	cd frontend && npm run test
	@echo "✓ Tests complete"

lint:
	@echo "Running linters..."
	cd backend && pylint app/
	cd frontend && npm run lint
	@echo "✓ Linting complete"

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf backend/.venv
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	@echo "✓ Cleaned"

test:
	cd backend && pytest

lint:
	cd backend && black app/
	cd backend && flake8 app/
	cd frontend && npm run lint

db-migrate:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

db-upgrade:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

shell:
	cd backend && python

format:
	cd backend && black app/ && isort app/
	cd frontend && npm run lint -- --fix

ps:
	docker-compose ps

restart:
	docker-compose restart

build:
	docker-compose build

.DEFAULT_GOAL := help
