resource "aws_apigatewayv2_authorizer" "cognito_authorizer" {

  name = "${local.project}-cognito-authorizer-${var.environment}"

  api_id = aws_apigatewayv2_api.receipt_api.id

  authorizer_type = "JWT"

  identity_sources = [
    "$request.header.Authorization"
  ]

  jwt_configuration {

    audience = [
      aws_cognito_user_pool_client.pwa_client.id
    ]

    issuer = "https://${aws_cognito_user_pool.receipt_users.endpoint}"
  }
}