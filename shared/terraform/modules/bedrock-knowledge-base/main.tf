# ============================================================================
# Bedrock Knowledge Base with S3 Vector Storage (using awscc provider)
# ============================================================================

resource "awscc_bedrock_knowledge_base" "this" {
  name     = var.knowledge_base_name
  role_arn = var.role_arn
  
  knowledge_base_configuration = {
    type = "VECTOR"
    vector_knowledge_base_configuration = {
      embedding_model_arn = var.embedding_model_arn
      embedding_model_configuration = {
        bedrock_embedding_model_configuration = {
          dimensions = 1024
        }
      }
    }
  }

  storage_configuration = {
    type = "S3_VECTORS"
    s3_vectors_configuration = {
      # index_arn         = var.index_arn # TODO: verify if index_arn can replace the two other attributes
      index_name        = var.index_name
      vector_bucket_arn = var.vector_bucket_arn
    }
  }

  tags = var.tags
}
