resource "aws_s3_bucket" "processed_receipts" {

  bucket = "${local.project}-processed-bucket-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-processed-bucket-${var.environment}"
    }
  )
}

resource "aws_lambda_permission" "csv_exporter_function_permission" {
  statement_id  = "AllowExecutionFromProcessedS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.csv_exporter_function.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.processed_receipts.arn
}

resource "aws_lambda_permission" "receipt_normalizer_function_permission" {
  statement_id  = "AllowExecutionFromProcessedS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt_normalizer_function.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.processed_receipts.arn
}

resource "aws_lambda_permission" "receipt_mailer_function_permission" {
  statement_id  = "AllowExecutionFromProcessedS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt_mailer_function.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.processed_receipts.arn
}

resource "aws_lambda_permission" "report_sender_function_permission" {
  statement_id  = "AllowExecutionFromProcessedS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.report_sender_function.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.processed_receipts.arn
}

resource "aws_s3_bucket_notification" "csv_exporter_function_trigger" {
  bucket = aws_s3_bucket.processed_receipts.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.csv_exporter_function.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix = "normalized/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_normalizer_function.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix = "textract/"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_mailer_function.arn
    events = [
      "s3:ObjectCreated:*"
    ]

    filter_prefix = "exports/receipts/"
    filter_suffix = ".csv"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.report_sender_function.arn
    events = [
      "s3:ObjectCreated:*"
    ]

    filter_prefix = "chatgpt/"
    filter_suffix = ".json"
  }

  depends_on = [
    aws_lambda_permission.csv_exporter_function_permission,
    aws_lambda_permission.receipt_normalizer_function_permission,
    aws_lambda_permission.receipt_mailer_function_permission,
    aws_lambda_permission.report_sender_function_permission
  ]
}
