resource "aws_s3_bucket" "uploader" {
  bucket = "${local.project}-uploader-${var.environment}"
  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-uploader-${var.environment}"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "uploader" {
  bucket = aws_s3_bucket.uploader.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "pwa" {
  bucket = aws_s3_bucket.uploader.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.uploader.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.uploader.arn
          }
        }
      }
    ]
  })
}