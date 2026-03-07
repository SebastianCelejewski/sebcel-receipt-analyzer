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