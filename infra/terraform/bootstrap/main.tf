terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

locals {
  project = "sebcel-receipt-analyzer"
}

resource "aws_s3_bucket" "terraform_state" {

  bucket = "${local.project}-terraform-state"

  tags = {
    Name        = "${local.project}-terraform-state"
    application = local.project
    environment = "global"
    owner       = "Sebastian.Celejewski@wp.pl"
    managed-by  = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {

  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_dynamodb_table" "terraform_locks" {

  name         = "${local.project}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "${local.project}-terraform-locks"
    application = local.project
    environment = "global"
    owner       = "Sebastian.Celejewski@wp.pl"
    managed-by  = "terraform"
  }
}