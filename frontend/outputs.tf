output "raw_bucket" {
  value = aws_s3_bucket.raw_receipts.id
}

output "processed_bucket" {
  value = aws_s3_bucket.processed_receipts.id
}