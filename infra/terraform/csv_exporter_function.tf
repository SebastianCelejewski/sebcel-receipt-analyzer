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