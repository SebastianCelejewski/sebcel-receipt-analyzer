.PHONY: setup install format lint check test pipeline-local infra-init infra-plan infra-apply infra-destroy package-functions deploy clean clean-all help

ENV ?= dev
PYTHON=python
VENV=.venv
VENV_PY=$(VENV)/Scripts/python
VENV_PIP=$(VENV)/Scripts/pip

BACKEND_DIR=backend
INFRA_DIR=infra/terraform
BUILD_DIR=build

PWA_BUCKET = sebcel-receipt-analyzer-uploader-$(ENV)
PWA_SRC_DIR = frontend/pwa
PWA_BUILD_DIR = frontend/pwa-build

VERSION_BASE=0.3.1
BUILD_TIME=$(shell date +"%Y-%m-%d_%H-%M-%S")
VERSION=$(VERSION_BASE).$(BUILD_TIME)

CF_DISTRIBUTION_ID=$(shell terraform -chdir=$(INFRA_DIR) output -raw cloudfront_distribution_id 2>/dev/null)

confirm-prod:
	@echo "[confirm-prod]"
	@if [ "$(ENV)" = "prod" ]; then \
		echo "Deployment to PROD!"; \
		read -p "Are you sure? (yes/no): " answer; \
		if [ "$$answer" != "yes" ]; then \
			echo "Deployment cancelled"; \
			exit 1; \
		fi; \
	fi

build-version:
	@echo "[build-version]"
	echo '{ "version": "$(VERSION)", "env": "$(ENV)" }' > frontend/pwa/version.json

prepare-config:
	@echo "[prepare-config]"
	cp frontend/pwa/config.$(ENV).js frontend/pwa/config.js

setup:
	@echo "[setup]"
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install -r requirements.txt

install:
	@echo "[install]"
	$(VENV_PIP) install -r requirements.txt

format:
	@echo "[format]"
	$(VENV_PY) -m black $(BACKEND_DIR)
	$(VENV_PY) -m isort $(BACKEND_DIR)

lint:
	@echo "[lint]"
	$(VENV_PY) -m flake8 $(BACKEND_DIR)

check: format lint

test:
	@echo "[test]"
	$(VENV_PY) -m pytest

pipeline-local:
	@echo "[pipeline-local]"
	$(VENV_PY) scripts/local_test_pipeline.py

infra-init:
	@echo "[infra-init]"
	cd $(INFRA_DIR) && terraform init

infra-plan:
	@echo "[infra-plan]"
	cd $(INFRA_DIR) && terraform plan

infra-apply: confirm-prod
	@echo "[infra-apply]"
	cd $(INFRA_DIR) && terraform init -backend-config=env/backend-$(ENV).hcl -reconfigure
	cd $(INFRA_DIR) && terraform apply -var-file=env/$(ENV).tfvars

infra-destroy:
	@echo "[infra-deploy]"
	cd $(INFRA_DIR) && terraform destroy
	
build-layer-openai:
	@echo "[build-layer-openai]"
	rm -rf backend/layers/openai_layer/python
	mkdir -p backend/layers/openai_layer/python

	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "$$(pwd -W)":/var/task \
		--entrypoint "" \
		public.ecr.aws/lambda/python:3.12 \
		pip install openai -t backend/layers/openai_layer/python

	cd backend/layers/openai_layer && zip -r ../../../build/openai_layer.zip .

build-layer-pymupdf:
	@echo "[build-layer-pymupdf]"
	rm -rf backend/layers/pymupdf/python
	mkdir -p backend/layers/pymupdf/python

	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "$$(pwd -W)":/var/task \
		--entrypoint "" \
		public.ecr.aws/lambda/python:3.12 \
		pip install pymupdf -t backend/layers/pymupdf_layer/python

	cd backend/layers/pymupdf_layer && zip -r ../../../build/pymupdf_layer.zip .

package-functions:
	@echo "[package-functions]"
	mkdir -p $(BUILD_DIR)
	cd backend/functions/textract_analyzer && zip -r ../../../$(BUILD_DIR)/textract_analyzer.zip .
	cd backend/functions/chatgpt_analyzer && zip -r ../../../$(BUILD_DIR)/chatgpt_analyzer.zip .
	cd backend/functions/receipt_normalizer && zip -r ../../../$(BUILD_DIR)/receipt_normalizer.zip .
	cd backend/functions/csv_exporter && zip -r ../../../$(BUILD_DIR)/csv_exporter.zip .
	cd backend/functions/upload_url_generator && zip -r ../../../$(BUILD_DIR)/upload_url_generator.zip .
	cd backend/functions/receipt_mailer && zip -r ../../../$(BUILD_DIR)/receipt_mailer.zip .
	cd backend/functions/report_sender && zip -r ../../../$(BUILD_DIR)/report_sender.zip .

build-pwa:
	@echo "[build-pwa]"
	rm -rf $(PWA_BUILD_DIR)
	mkdir -p $(PWA_BUILD_DIR)

	# Copy src files to build dir
	cp -r $(PWA_SRC_DIR)/* $(PWA_BUILD_DIR)/

	# Replace version
	sed -i 's/__VERSION__/$(VERSION)/g' $(PWA_BUILD_DIR)/index.html

	# Pick config
	cp $(PWA_SRC_DIR)/config.$(ENV).js $(PWA_BUILD_DIR)/config.js

deploy-pwa: confirm-prod build-version build-pwa prepare-config
	@echo "[deploy-pwa]"
	aws s3 sync $(PWA_BUILD_DIR) s3://$(PWA_BUCKET) \
		--delete \
		--exclude "*.html" \
		--cache-control "max-age=31536000,public"

	aws s3 sync $(PWA_BUILD_DIR) s3://$(PWA_BUCKET) \
		--exclude "*" \
		--include "*.html" \
		--cache-control "no-cache"

	aws cloudfront create-invalidation \
		--distribution-id $(CF_DISTRIBUTION_ID) \
		--paths "/*"

pwa-url:
	terraform -chdir=infra/terraform output uploader_website_url		

deploy: package-functions infra-apply deploy-pwa

deploy-dev:
	@echo "[deploy-dev]"
	$(MAKE) ENV=dev deploy

deploy-prod:
	@echo "[deploy-prod]"
	$(MAKE) ENV=prod deploy

clean:
	@echo "[clean]"
	rm -rf $(BUILD_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache

clean-all: clean
	@echo "[clean-all]"
	rm -rf $(VENV)

show-env:
	@echo "[show-env]"
	@echo "ENV=$(ENV)"
	@echo "BUCKET=$(PWA_BUCKET)"

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
