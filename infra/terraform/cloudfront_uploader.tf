resource "aws_cloudfront_distribution" "uploader" {
  enabled = true

  origin {
    domain_name = aws_s3_bucket.uploader.bucket_regional_domain_name
    origin_id = "uploader-s3-origin"
  }

  default_root_object = "index.html"

  default_cache_behavior {
    target_origin_id = "uploader-s3-origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]

    cached_methods = ["GET","HEAD"]

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project}-uploader-cdn-${var.environment}"
    }
  )

}