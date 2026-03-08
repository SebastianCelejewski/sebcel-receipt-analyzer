resource "aws_cognito_user_pool" "receipt_users" {

  name = "${local.project}-users-${var.environment}"

  username_attributes = ["email"]

  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length = 8
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-users-${var.environment}"
    }
  )
}

resource "aws_cognito_user_pool_client" "pwa_client" {

  name = "${local.project}-pwa-client-${var.environment}"

  user_pool_id = aws_cognito_user_pool.receipt_users.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  callback_urls = [
    local.uploader_url
  ]

  logout_urls = [
    local.uploader_url
  ]
  
  allowed_oauth_flows_user_pool_client = true

  allowed_oauth_flows = [
    "implicit"
  ]

  allowed_oauth_scopes = [
    "email",
    "openid",
    "profile"
  ]
}

resource "aws_cognito_user_pool_domain" "receipt_domain" {
  domain       = "${local.project}-${var.environment}"
  user_pool_id = aws_cognito_user_pool.receipt_users.id
}