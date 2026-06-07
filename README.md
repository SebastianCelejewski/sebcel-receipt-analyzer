# Sebcel Receipt Analyzer

**Receipt Analyzer** is a personal data pipeline for analyzing household expenses from shopping receipts.

The system allows household members to quickly capture photos of receipts using a mobile device, upload them to the cloud, automatically extract structured purchase data, and generate datasets for financial analysis.

The project focuses on practical automation of receipt processing rather than manual bookkeeping and is implemented as a lightweight serverless system using AWS.

---

# Project Goals

- Collect shopping receipts from multiple household members
- Automatically extract structured purchase data
- Normalize product names, quantities, and prices
- Categorize purchases
- Generate datasets for expense analysis
- Support household budgeting and spending insights

---

# Architecture Overview

The system consists of three main components:

## 1. Receipt Capture (PWA)

`frontend/pwa` — a Progressive Web App used to capture photos of receipts on a
mobile or desktop device.

The app authenticates the user (Cognito), requests a presigned upload URL from
the backend, and uploads the image directly to cloud storage.

Typical workflow:

User → Photo of receipt → Upload to S3 (raw bucket)

---

## 2. Cloud Processing Pipeline

`backend/functions` — a serverless backend (AWS Lambda) that automatically
processes uploaded receipts: storage, AI-based data extraction, JSON
generation, and email notifications.

Typical pipeline:

Receipt image (S3 raw bucket)
↓
AWS Lambda trigger (via SNS)
↓
ChatGPT Vision analysis (Polish-aware prompt) / Amazon Textract (OCR)
↓
Structured JSON saved to S3 (processed bucket)
↓
Email notification with the extracted data (receipt_mailer / report_sender)


Technologies used:

- AWS S3 — receipt and result storage
- AWS Lambda — serverless processing
- OpenAI GPT-4 Vision — receipt/invoice parsing (primary)
- Amazon Textract — receipt OCR and extraction (alternative path)
- AWS SES/SMTP — email notifications
- JSON — structured output format

---

## 3. Local Reporting Tools (CLI)

`cli/receipt_processor` — a console application that turns the structured JSON
data into CSV datasets ready for analysis (e.g. in Excel).

This currently runs locally (on the household's computer) rather than in the
cloud, because in practice the resulting datasets are consumed locally (in
Excel) and downloading/merging cloud-generated CSVs by hand proved
inconvenient. Running the report generation locally also makes it trivial to
iterate on normalization/categorization rules without redeploying Lambdas.

### Installation

The CLI is a regular Python package (`cli/receipt_processor`) that registers
its commands as console scripts. To install it (e.g. on Windows, so the
commands are available globally as `receipt-upload`, `receipt-download`,
`receipt-process`, `receipt-report`):

```sh
pip install cli/receipt_processor
```

For active development, install it in editable mode instead — code changes
take effect immediately without reinstalling:

```sh
pip install -e cli/receipt_processor
```

Requirements:

- Python 3.11+
- An `OPENAI_API_KEY` available to the `openai` SDK (used by `receipt-process`
  for files that haven't been analyzed in the cloud yet)
- AWS credentials configured (e.g. via `aws configure` / `AWS_PROFILE`) with
  access to the raw and processed S3 buckets — used by `receipt-upload` and
  `receipt-download`

### Typical workflow

```
receipt-upload invoice1.pdf invoice2.pdf  # send PDF invoices (e.g. received by e-mail) to the cloud raw bucket,
                                           # the same way the PWA uploads photos, so they enter the same pipeline
receipt-download 2026-06-07                # fetch source files + JSON results from S3 for a given date
receipt-process .                          # analyze any new files (skips files already processed in the cloud)
receipt-report .                           # build CSV summary/details reports from JSON data
```

The tool reuses the structured JSON produced by the cloud pipeline whenever
available (matching files by name), so OpenAI is only called for files that
haven't been analyzed yet — avoiding duplicate API costs.

### Commands

| Command | Purpose | Example |
|---|---|---|
| `receipt-upload` | Upload local files (e.g. PDF invoices) to the cloud raw bucket | `receipt-upload --env prod invoice1.pdf invoice2.pdf` |
| `receipt-download` | Download source files + JSON results for a given date from S3 | `receipt-download 2026-06-07 --env prod` |
| `receipt-process` | Analyze receipts in a folder (calls OpenAI; skips files that already have a JSON result, whether produced locally or in the cloud) | `receipt-process .` |
| `receipt-report` | Build CSV summary/details reports from JSON data in a folder | `receipt-report .` |

Run any command with `--help` to see its full set of options (e.g. `--env`,
`--output`, `--user`).

> **Future direction:** CSV/report generation may eventually move into the
> cloud pipeline as well (see `csv_exporter` Lambda), once a more convenient
> way of consuming the resulting datasets locally (e.g. automatic sync,
> dashboards) is in place. For now, the CLI is the practical, low-friction
> choice for this stage.

---

## 4. Expense Analysis

Processed datasets can be analyzed using standard tools such as:

- Excel
- Python notebooks
- SQL queries
- BI dashboards

Example analyses:

- spending by category
- spending by store
- monthly household expenses
- grocery price trends


---

# Data Model

The core dataset is built around **individual purchase items extracted from receipts**.

Example structure:

| date | store | product | quantity | unit_price | total_price | category |
|-----|-----|-----|-----|-----|-----|-----|
| 2026-03-05 | Biedronka | Milk UHT 3.2% | 2 | 3.49 | 6.98 | dairy |
| 2026-03-05 | Biedronka | Bananas | 0.62 kg | 5.99 | 3.71 | fruit |

---

# Typical Workflow

1. Household member takes a photo of a receipt using the PWA
2. Image is uploaded to cloud storage (S3 raw bucket)
3. The cloud processing pipeline extracts purchase data (OpenAI / Textract)
   and stores structured JSON in the processed bucket; an email notification
   is sent with the extracted data
4. Periodically (e.g. weekly), the household downloads that period's source
   files and JSON results using the `cli/receipt_processor` CLI
   (`receipt-download`), runs analysis on any new files (`receipt-process`),
   and generates CSV reports (`receipt-report`)
5. Data is analyzed in Excel or other tools

---

# Design Principles

- Serverless architecture
- Low operational cost
- Simple data pipeline
- Easy extensibility
- Minimal user interaction
- Reproducible infrastructure

---

# Possible Extensions

Future improvements may include:

- automatic product categorization
- price tracking and inflation analysis
- dashboards and visualizations
- mobile application
- product database and normalization dictionary
- duplicate receipt detection

---

# AWS Resource Naming and Tagging Conventions

This project uses consistent naming and tagging conventions for all AWS resources to ensure clarity, maintainability, and proper cost attribution.

---

## Resource Naming Convention

All AWS resources follow the format:

sebcel-receipt-analyzer-<component>-<resource>-<environment>


### Components

| Part | Description | Example |
|-----|-------------|--------|
| project | Project identifier | `sebcel-receipt-analyzer` |
| component | Logical system component | `ingest`, `parser`, `export`, `storage` |
| resource | Type of AWS resource | `function`, `bucket`, `role` |
| environment | Deployment environment | `dev`, `test`, `prod` |

---

### Examples

#### Lambda functions

sebcel-receipt-analyzer-ingest-function-dev
sebcel-receipt-analyzer-parser-function-dev
sebcel-receipt-analyzer-export-function-dev

#### S3 buckets

sebcel-receipt-analyzer-raw-bucket-dev
sebcel-receipt-analyzer-processed-bucket-dev

#### IAM roles

sebcel-receipt-analyzer-lambda-role-dev


---

## AWS Tagging Convention

All resources must include the following tags.

| Tag | Purpose |
|----|--------|
| `Name` | Human-readable resource name |
| `application` | Used for cost allocation and grouping |
| `environment` | Deployment environment (`dev`, `test`, `prod`) |
| `owner` | Resource owner |
| `managed-by` | Indicates infrastructure management tool |

---

### Standard Tag Set

Name = <resource-name>
application = sebcel-receipt-analyzer
environment = <environment>
owner = Sebastian.Celejewski@wp.pl
managed-by = terraform


Example:

Name = sebcel-receipt-analyzer-ingest-function-dev
application = sebcel-receipt-analyzer
environment = dev
owner = Sebastian.Celejewski@wp.pl

managed-by = terraform


---

## Terraform Implementation

To ensure consistency, Terraform uses centralized variables and locals.

Example:

```hcl
locals {
  project = "sebcel-receipt-analyzer"

  common_tags = {
    application = local.project
    environment = var.environment
    owner       = "Sebastian.Celejewski@wp.pl"
    managed-by  = "terraform"
  }
}

Notes

S3 bucket names must be globally unique within AWS.

The project prefix sebcel- is used to help ensure uniqueness.

All infrastructure is managed using Terraform.

These conventions should be applied consistently across all AWS resources.