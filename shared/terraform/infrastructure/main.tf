# ============================================================================
# Shared S3 Bucket for All Agent Source Code
# ============================================================================

module "agents_code_bucket" {
  source           = "../modules/s3"
  s3_bucket_prefix = "tf-${var.project_name}-code-"
}

# ============================================================================
# Shared S3 Bucket for Knowledge Base Documents
# ============================================================================

module "kb_documents_bucket" {
  source           = "../modules/s3"
  s3_bucket_prefix = "tf-${var.project_name}-kb-docs-"
}
