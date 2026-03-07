resource "aws_lambda_permission" "textract_analyzer_function_permission" {

  statement_id  = "AllowExecutionFromS3"

  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.textract_analyzer_function.function_name

  principal = "s3.amazonaws.com"

  source_arn = aws_s3_bucket.raw_receipts.arn
}

resource "aws_s3_bucket_notification" "textract_analyzer_function_trigger" {

  bucket = aws_s3_bucket.raw_receipts.id

  lambda_function {

    lambda_function_arn = aws_lambda_function.textract_analyzer_function.arn

    events = [
      "s3:ObjectCreated:*"
    ]
  }

  depends_on = [
    aws_lambda_permission.textract_analyzer_function_permission
  ]
}