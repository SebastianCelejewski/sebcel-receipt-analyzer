resource "aws_lambda_permission" "allow_s3_invoke" {

  statement_id  = "AllowExecutionFromS3"

  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name

  principal = "s3.amazonaws.com"

  source_arn = aws_s3_bucket.raw_receipts.arn
}

resource "aws_s3_bucket_notification" "receipt_upload_trigger" {

  bucket = aws_s3_bucket.raw_receipts.id

  lambda_function {

    lambda_function_arn = aws_lambda_function.ingest.arn

    events = [
      "s3:ObjectCreated:*"
    ]
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke
  ]
}