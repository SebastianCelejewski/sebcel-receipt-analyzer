.PHONY: setup install format lint check test pipeline-local infra-init infra-plan infra-apply infra-destroy package-functions deploy clean clean-all help

PYTHON=python
VENV=.venv
VENV_PY=$(VENV)/Scripts/python
VENV_PIP=$(VENV)/Scripts/pip

BACKEND_DIR=backend
INFRA_DIR=infra/terraform
BUILD_DIR=build

PWA_BUCKET = sebcel-receipt-analyzer-uploader-dev
PWA_DIR = frontend/pwa

VERSION_BASE=0.1.11
BUILD_TIME=$(shell date +"%Y-%m-%d_%H-%M-%S")
VERSION=$(VERSION_BASE).$(BUILD_TIME)

build-version:
	echo '{ "version": "$(VERSION)" }' > frontend/pwa/version.json

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

package-functions:
	mkdir -p $(BUILD_DIR)
	cd backend/functions/textract_analyzer && zip -r ../../../$(BUILD_DIR)/textract_analyzer.zip .
	cd backend/functions/receipt_normalizer && zip -r ../../../$(BUILD_DIR)/receipt_normalizer.zip .
	cd backend/functions/csv_exporter && zip -r ../../../$(BUILD_DIR)/csv_exporter.zip .
	cd backend/functions/upload_url_generator && zip -r ../../../$(BUILD_DIR)/upload_url_generator.zip .

deploy-pwa: build-version
	aws s3 sync $(PWA_DIR) s3://$(PWA_BUCKET) \
		--delete \
		--exclude "*.html"

	aws s3 sync $(PWA_DIR) s3://$(PWA_BUCKET) \
		--exclude "*" \
		--include "*.html" \
		--cache-control "no-cache"

pwa-url:
	terraform -chdir=infra/terraform output uploader_website_url		

deploy: package-functions infra-apply deploy-pwa

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
	@echo "  make package-functions"
	@echo "  make deploy"
	@echo "  make clean"
	@echo "  make clean-all"
	@echo ""
