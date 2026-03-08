locals {

  project = "sebcel-receipt-analyzer"

  common_tags = {

    application = local.project
    environment = var.environment
    owner       = "Sebastian.Celejewski@wp.pl"
    managed-by  = "terraform"
  }

  uploader_url = "https://${aws_cloudfront_distribution.uploader.domain_name}"

}