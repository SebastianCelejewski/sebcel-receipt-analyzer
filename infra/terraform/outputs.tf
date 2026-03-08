output "raw_bucket" {
  value = aws_s3_bucket.raw_receipts.id
}

output "processed_bucket" {
  value = aws_s3_bucket.processed_receipts.id
}

output "receipt_api_url" {
  value = aws_apigatewayv2_api.receipt_api.api_endpoint
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.receipt_users.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.pwa_client.id
}

output "cognito_login_domain" {
  value = aws_cognito_user_pool_domain.receipt_domain.domain
}