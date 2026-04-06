resource "aws_s3_bucket" "raw_receipts" {

  bucket = "${local.project}-raw-bucket-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-raw-bucket-${var.environment}"
    }
  )
}

resource "aws_s3_bucket_cors_configuration" "raw_receipts" {
  bucket = aws_s3_bucket.raw_receipts.id

  cors_rule {
    allowed_methods = [
      "PUT"
    ]
    allowed_origins = [
      "*"
    ]
    allowed_headers = [
      "*"
    ]
    expose_headers = [
      "ETag"
    ]

    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_notification" "raw_bucket_trigers" {
  bucket = aws_s3_bucket.raw_receipts.id

  topic {
    topic_arn = aws_sns_topic.receipt_uploaded.arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [
    aws_sns_topic_policy.allow_s3
  ]
}

