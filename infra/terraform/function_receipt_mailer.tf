resource "aws_lambda_function" "receipt_mailer_function" {

  function_name = "${local.project}-receipt-mailer-function-${var.environment}"

  filename         = "../../build/receipt_mailer.zip"
  source_code_hash = filebase64sha256("../../build/receipt_mailer.zip")

  handler = "handler.handler"
  runtime = "python3.12"

  role = aws_iam_role.receipt_mailer_function_role.arn

  timeout = 30
  memory_size = 256

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_receipts.bucket
      RAW_BUCKET = aws_s3_bucket.raw_receipts.bucket
      SES_SENDER = "Sebastian.Celejewski@wp.pl"
      SMTP_USERNAME_PARAM = aws_ssm_parameter.smtp_username.name
      SMTP_PASSWORD_PARAM = aws_ssm_parameter.smtp_password.name
      RECIPIENTS = join(",", var.notification_emails)
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-receipt-mailer-function-${var.environment}"
    }
  )
}

resource "aws_iam_role" "receipt_mailer_function_role" {
  name = "${local.project}-receipt-mailer-function-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-receipt-mailer-function-role-${var.environment}"
    }
  )
}

resource "aws_iam_role_policy" "receipt_mailer_function_ses_policy" {
  name = "${local.project}-receipt-mailer-function-ses-policy-${var.environment}"
  role = aws_iam_role.receipt_mailer_function_role.id
  policy = jsonencode({
    Version = "2012-10-17"
      Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = ["${aws_s3_bucket.raw_receipts.arn}/*", "${aws_s3_bucket.raw_receipts.arn}"]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = ["${aws_s3_bucket.processed_receipts.arn}/*", "${aws_s3_bucket.processed_receipts.arn}"]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "receipt_mailer_function_ssm_read_policy" {

  name = "${local.project}-receipt-mailer-function-ssm-read-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          aws_ssm_parameter.smtp_username.arn,
          aws_ssm_parameter.smtp_password.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "receipt_mailer_function_policy_attachment_basic_logs" {
  role       = aws_iam_role.receipt_mailer_function_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


resource "aws_iam_role_policy_attachment" "receipt_mailer_function_policy_attachment_ssm_read" {
  role = aws_iam_role.receipt_mailer_function_role.name
  policy_arn = aws_iam_policy.receipt_mailer_function_ssm_read_policy.arn
}