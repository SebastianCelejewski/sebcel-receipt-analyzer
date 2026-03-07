resource "aws_iam_role" "textract_analyzer_function_role" {

  name = "${local.project}-textract-analyzer-function-role-${var.environment}"

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
      Name = "${local.project}-textract-analyzer-function-role-${var.environment}"
    }
  )
}

resource "aws_iam_role_policy_attachment" "textract_analyser_function_policy_attachment_basic_logs" {
  role       = aws_iam_role.textract_analyzer_function_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "textract_analyser_function_policy" {
  name = "${local.project}-textract-analyser-function-policy-${var.environment}"
  role = aws_iam_role.textract_analyzer_function_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
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
          "textract:AnalyzeExpense"
        ]
        Resource = "*"
      }

    ]
  })
}