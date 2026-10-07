.PHONY: help install lint format test test-cov security docker-build docker-up docker-down k8s-deploy tf-plan

help: ## Display available commands
	@echo "Hybrid Telemetry Observability Pipeline - Operations Makefile"
	@echo "=============================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install development & runtime dependencies
	pip install --upgrade pip
	pip install -r requirements.txt -r requirements-dev.txt

lint: ## Run linters and type checkers (Ruff & MyPy)
	ruff check src/ tests/
	mypy src/

format: ## Format code with Ruff and Black
	ruff check --fix src/ tests/
	black src/ tests/

test: ## Run unit tests
	pytest tests/ -v

test-cov: ## Run unit tests with coverage reporting
	pytest --cov=src --cov-report=term-missing --cov-report=html tests/

security: ## Run static security scanner (Bandit)
	bandit -r src/ -ll

docker-build: ## Build hardened multi-stage Docker container
	docker build -f docker/Dockerfile -t hybrid-telemetry-pipeline:latest .

docker-up: ## Spin up pipeline, Prometheus, and Grafana via Docker Compose
	docker compose -f docker/docker-compose.yml up -d --build

docker-down: ## Stop and tear down local Docker Compose stack
	docker compose -f docker/docker-compose.yml down -v

k8s-deploy: ## Deploy manifests via Kustomize
	kubectl apply -k k8s/

k8s-delete: ## Teardown Kubernetes resources
	kubectl delete -k k8s/

tf-init: ## Initialize Terraform providers and backend
	cd terraform && terraform init

tf-plan: ## Run Terraform plan
	cd terraform && terraform plan

tf-apply: ## Run Terraform apply
	cd terraform && terraform apply -auto-approve
