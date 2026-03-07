.PHONY: setup install format lint check test pipeline-local infra-init infra-plan infra-apply infra-destroy package-lambdas deploy clean clean-all help

PYTHON=python
VENV=.venv
VENV_PY=$(VENV)/Scripts/python
VENV_PIP=$(VENV)/Scripts/pip

BACKEND_DIR=backend
INFRA_DIR=infra/terraform
BUILD_DIR=build

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install -r requirements.txt

install:
	$(VENV_PIP) install -r requirements.txt

format:
	$(VENV_PY) -m black $(BACKEND_DIR)
	$(VENV_PY) -m isort $(BACKEND_DIR)

lint:
	$(VENV_PY) -m flake8 $(BACKEND_DIR)

check: format lint

test:
	$(VENV_PY) -m pytest

pipeline-local:
	$(VENV_PY) scripts/local_test_pipeline.py

infra-init:
	cd $(INFRA_DIR) && terraform init

infra-plan:
	cd $(INFRA_DIR) && terraform plan

infra-apply:
	cd $(INFRA_DIR) && terraform apply

infra-destroy:
	cd $(INFRA_DIR) && terraform destroy

package-lambdas:
	mkdir -p $(BUILD_DIR)
	cd backend/lambdas/textract_analyzer && zip -r ../../../$(BUILD_DIR)/textract_analyzer.zip .
	cd backend/lambdas/receipt_normalizer && zip -r ../../../$(BUILD_DIR)/receipt_normalizer.zip .
	cd backend/lambdas/csv_exporter && zip -r ../../../$(BUILD_DIR)/csv_exporter.zip .

deploy: package-lambdas infra-apply

clean:
	rm -rf $(BUILD_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache

clean-all: clean
	rm -rf $(VENV)

help:
	@echo ""
	@echo "Available commands:"
	@echo "  make setup"
	@echo "  make install"
	@echo "  make format"
	@echo "  make lint"
	@echo "  make check"
	@echo "  make test"
	@echo "  make pipeline-local"
	@echo "  make infra-init"
	@echo "  make infra-plan"
	@echo "  make infra-apply"
	@echo "  make infra-destroy"
	@echo "  make package-lambdas"
	@echo "  make deploy"
	@echo "  make clean"
	@echo "  make clean-all"
	@echo ""
