resource "aws_lambda_function" "chatgpt_analyzer_function" {

  function_name = "${local.project}-chatpgt-analyser-function-${var.environment}"

  filename = "../../build/chatgpt_analyzer.zip"
  source_code_hash = filebase64sha256("../../build/chatgpt_analyzer.zip")

  runtime = "python3.12"
  handler = "handler.handler"
  timeout = 60

  role = aws_iam_role.chatgpt_analyzer_function_role.arn

  layers = [
    aws_lambda_layer_version.openai.arn,
    aws_lambda_layer_version.pymupdf.arn
  ]

  environment {
    variables = {
      PROCESSED_BUCKET = aws_s3_bucket.processed_receipts.id
      OPENAI_API_KEY_PARAMETER_NAME = aws_ssm_parameter.openai_api_key.name
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-chatgpt-analyser-function-${var.environment}"
    }
  )
}

resource "aws_iam_role" "chatgpt_analyzer_function_role" {

  name = "${local.project}-chatgpt-analyzer-function-role-${var.environment}"

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
      Name = "${local.project}-chatgpt-analyzer-function-role-${var.environment}"
    }
  )
}

resource "aws_iam_role_policy_attachment" "chatgpt_analyser_function_policy_attachment_basic_logs" {
  role       = aws_iam_role.chatgpt_analyzer_function_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "chatgpt_analyser_function_policy" {
  name = "${local.project}-chatgpt-analyser-function-policy-${var.environment}"
  role = aws_iam_role.chatgpt_analyzer_function_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.raw_receipts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.processed_receipts.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = aws_ssm_parameter.openai_api_key.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })
}