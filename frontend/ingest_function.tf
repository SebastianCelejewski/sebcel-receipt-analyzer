resource "aws_lambda_function" "ingest" {

  function_name = "${local.project}-ingest-function-${var.environment}"

  filename = "../../build/textract_analyzer.zip"

  runtime = "python3.12"

  handler = "handler.handler"

  role = aws_iam_role.lambda_role.arn

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-ingest-function-${var.environment}"
    }
  )
}