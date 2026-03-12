resource "aws_lambda_function" "receipt_normalizer_function" {

  function_name = "${local.project}-receipt-normalizer-function-${var.environment}"

  filename = "../../build/receipt_normalizer.zip"
  source_code_hash = filebase64sha256("../../build/receipt_normalizer.zip")

  runtime = "python3.12"
  handler = "handler.handler"

  role = aws_iam_role.receipt_normalizer_function_role.arn

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_receipts.id
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-receipt-normalizer-function-${var.environment}"
    }
  )
}

resource "aws_iam_role" "receipt_normalizer_function_role" {
  name = "${local.project}-receipt-normalizer-function-role-${var.environment}"
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
      Name = "${local.project}-receipt-normalizer-function-role-${var.environment}"
    }
  )
}

resource "aws_iam_role_policy_attachment" "receipt_normalizer_function_policy_attachment_basic_logs" {
  role       = aws_iam_role.receipt_normalizer_function_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "receipt_normalizer_function_policy" {
  name = "${local.project}-receipt-normalizer-function-policy-${var.environment}"
  role = aws_iam_role.receipt_normalizer_function_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.processed_receipts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.processed_receipts.arn}/*"
      }
    ]
  })
}