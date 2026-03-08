resource "aws_s3_bucket" "uploader" {

  bucket = "${local.project}-uploader-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-uploader-${var.environment}"
    }
  )
}


resource "aws_s3_bucket_website_configuration" "uploader" {

  bucket = aws_s3_bucket.uploader.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}


resource "aws_s3_bucket_public_access_block" "uploader" {

  bucket = aws_s3_bucket.uploader.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}


resource "aws_s3_bucket_policy" "uploader_public_read" {

  bucket = aws_s3_bucket.uploader.id

  policy = jsonencode({

    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.uploader.arn}/*"
      }
    ]
  })
}