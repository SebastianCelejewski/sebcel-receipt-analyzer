resource "aws_lambda_function" "ingest" {

  function_name = "${local.project}-ingest-function-${var.environment}"

  filename = "../../build/textract_analyzer.zip"

  runtime = "python3.12"

  source_code_hash = filebase64sha256("../../build/textract_analyzer.zip")

  handler = "handler.handler"

  role = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_receipts.id
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-ingest-function-${var.environment}"
    }
  )
}
