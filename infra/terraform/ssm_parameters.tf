resource "aws_ssm_parameter" "smtp_username" {

  name  = "/${local.project}/${var.environment}/smtp/username"
  type  = "String"
  value = var.smtp_user

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-smtp-username-${var.environment}"
    }
  )
}

resource "aws_ssm_parameter" "smtp_password" {

  name  = "/${local.project}/${var.environment}/smtp/password"
  type  = "SecureString"
  value = var.smtp_password

  lifecycle {
    ignore_changes = [
      value
    ]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-smtp-password-${var.environment}"
    }
  )
}

resource "aws_ssm_parameter" "openai_api_key" {

  name  = "/${local.project}/${var.environment}/openai/api_key"
  type  = "SecureString"
  value = var.openai_api_key

  lifecycle {
    ignore_changes = [
      value
    ]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-openai-api-key-${var.environment}"
    }
  )
}