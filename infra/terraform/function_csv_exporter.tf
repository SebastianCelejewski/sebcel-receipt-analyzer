resource "aws_lambda_function" "csv_exporter_function" {

  function_name = "${local.project}-csv-exporter-function-${var.environment}"

  role = aws_iam_role.csv_exporter_function_role.arn

  runtime = "python3.12"
  handler = "handler.handler"

  filename = "${path.module}/../../build/csv_exporter.zip"

  source_code_hash = filebase64sha256("${path.module}/../../build/csv_exporter.zip")

  timeout = 30

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_receipts.bucket
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-csv-exporter-function-${var.environment}"
    }
  )
}

resource "aws_iam_role" "csv_exporter_function_role" {

  name = "${local.project}-csv-exporter-function-role-${var.environment}"

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
      Name = "${local.project}-csv-exporter-function-role-${var.environment}"
    }
  )
}

resource "aws_iam_role_policy_attachment" "csv_exporter_function_policy_attachment_basic_logs" {
  role       = aws_iam_role.csv_exporter_function_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "csv_exporter_function_policy" {
  name = "${local.project}-csv-exporter-function-policy-${var.environment}"
  role = aws_iam_role.csv_exporter_function_role.id
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