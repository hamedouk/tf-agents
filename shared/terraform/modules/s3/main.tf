# ============================================================================
# S3 Buckets for Agent Source Code (CDK Asset Equivalent)
# ============================================================================

# Source Bucket
resource "aws_s3_bucket" "source" {
  bucket_prefix = var.s3_bucket_prefix
  force_destroy = true

  tags = {
    Name    = "${var.s3_bucket_prefix}"
    Purpose = "Store agents source code for CodeBuild"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "source" {
  bucket = aws_s3_bucket.source.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "source" {
  bucket = aws_s3_bucket.source.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# Enable versioning
resource "aws_s3_bucket_versioning" "source" {
  bucket = aws_s3_bucket.source.id

  versioning_configuration {
    status = "Enabled"
  }
}