# ============================================================================
# S3 Vector Bucket for Bedrock Knowledge Base
# ============================================================================

resource "awscc_s3vectors_vector_bucket" "this" {
  vector_bucket_name = var.vector_bucket_name

  encryption_configuration = {
    sse_type = var.sse_type
    kms_key_arn = var.kms_key_arn
  }
}

# ============================================================================
# S3 Vector Index
# ============================================================================

resource "awscc_s3vectors_index" "this" {
  vector_bucket_arn = awscc_s3vectors_vector_bucket.this.vector_bucket_arn
  index_name        = var.index_name
  dimension         = var.dimension
  data_type         = var.data_type
  distance_metric   = var.distance_metric

  metadata_configuration = var.non_filterable_metadata_keys != null ? {
    non_filterable_metadata_keys = var.non_filterable_metadata_keys
  } : null
}

# ============================================================================
# S3 Vector Bucket Policy
# ============================================================================
resource "awscc_s3vectors_vector_bucket_policy" "this" {
    policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Principal = {
            AWS = var.kb_role_arn
        }
        Effect = "Allow"
        Action = [
        "s3vectors:GetVectors",
        "s3vectors:PutVectors",
        "s3vectors:DeleteVectors"
        ]
        Resource = awscc_s3vectors_index.this.index_arn
      }
      ]})
    vector_bucket_arn = awscc_s3vectors_vector_bucket.this.vector_bucket_arn
}
