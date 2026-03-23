terraform {
  backend "s3" {
    bucket         = "sebcel-receipt-analyzer-terraform-state"
    region         = "eu-central-1"
    dynamodb_table = "sebcel-receipt-analyzer-terraform-locks"
    encrypt = true
  }
}