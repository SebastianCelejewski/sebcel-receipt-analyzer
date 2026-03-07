resource "aws_s3_bucket" "raw_receipts" {

  bucket = "${local.project}-raw-bucket-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-raw-bucket-${var.environment}"
    }
  )
}

resource "aws_s3_bucket" "processed_receipts" {

  bucket = "${local.project}-processed-bucket-${var.environment}"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-processed-bucket-${var.environment}"
    }
  )
}