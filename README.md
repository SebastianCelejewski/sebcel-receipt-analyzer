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

## 1. Receipt Capture

Users take photos of receipts using a simple mobile or web interface.

The application uploads images directly to cloud storage.

Typical workflow:

User → Photo of receipt → Upload to S3

---

## 2. Processing Pipeline

A serverless backend automatically processes uploaded receipts.

Typical pipeline:

eceipt image (S3)
↓
AWS Lambda trigger
↓
Amazon Textract (OCR + receipt structure)
↓
Normalization / AI parsing
↓
Structured JSON
↓
CSV dataset generation


Technologies used:

- AWS S3 — receipt storage
- AWS Lambda — serverless processing
- Amazon Textract — receipt OCR and extraction
- AI models — normalization and classification
- CSV / JSON — output data format

---

## 3. Expense Analysis

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

1. Household member takes a photo of a receipt
2. Image is uploaded to cloud storage
3. Processing pipeline extracts purchase data
4. Items are normalized and categorized
5. CSV dataset is generated
6. Data is analyzed in Excel or other tools

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