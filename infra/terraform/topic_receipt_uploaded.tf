resource "aws_sns_topic" "receipt_uploaded" {
  name = "receipt-uploaded"
}

resource "aws_sns_topic_policy" "allow_s3" {
  arn = aws_sns_topic.receipt_uploaded.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sns:Publish"
        Resource = aws_sns_topic.receipt_uploaded.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = aws_s3_bucket.raw_receipts.arn
          }
        }
      }
    ]
  })
}

resource "aws_sns_topic_subscription" "textract" {
  topic_arn = aws_sns_topic.receipt_uploaded.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.textract_analyzer_function.arn
}

resource "aws_sns_topic_subscription" "openai" {
  topic_arn = aws_sns_topic.receipt_uploaded.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.chatgpt_analyzer_function.arn
}

resource "aws_lambda_permission" "allow_sns_run_textract_analysis" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.textract_analyzer_function.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.receipt_uploaded.arn
}

resource "aws_lambda_permission" "allow_sns_run_chatgpt_analysis" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chatgpt_analyzer_function.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.receipt_uploaded.arn
}