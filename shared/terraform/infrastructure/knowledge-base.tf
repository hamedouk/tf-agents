# ============================================================================
# IAM Role for Knowledge Base
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "knowledge_base" {
  name = "${var.project_name}-kb-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:bedrock:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "knowledge_base" {
  name = "${var.project_name}-kb-policy"
  role = aws_iam_role.knowledge_base.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
      },
      {
        Effect = "Allow"
        Action = [
          "s3vectors:GetVectorBucket",
          "s3vectors:GetIndex",
          "s3vectors:PutVectors",
          "s3vectors:ListVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors",
          "s3vectors:QueryVectors"
        ]
        Resource = [
          module.vector_store.vector_bucket_arn,
          module.vector_store.index_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.kb_documents_bucket.s3_bucket_arn,
          "${module.kb_documents_bucket.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# ============================================================================
# Shared S3 Vector Store for Knowledge Base
# ============================================================================

module "vector_store" {
  source = "../modules/s3-vector-store"
  
  vector_bucket_name = "${var.project_name}-kb-vectors-${var.environment}"
  index_name         = "${var.project_name}-kb-index"
  dimension          = 1024  # titan-embed-text-v2 dimensions
  distance_metric    = "cosine"
  data_type          = "float32"
  kb_role_arn        = aws_iam_role.knowledge_base.arn
  non_filterable_metadata_keys = [
    "AMAZON_BEDROCK_METADATA",
    "AMAZON_BEDROCK_TEXT"
  ]

}


# ============================================================================
# Bedrock Knowledge Base
# ============================================================================

module "knowledge_base" {
  source = "../modules/bedrock-knowledge-base"
  
  knowledge_base_name = "${var.project_name}-kb-${var.environment}"
  description         = "Shared knowledge base for all agents"
  role_arn            = aws_iam_role.knowledge_base.arn
  vector_bucket_arn   = module.vector_store.vector_bucket_arn
  index_name          = module.vector_store.index_name
  index_arn           = module.vector_store.index_arn
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }

  depends_on = [
     module.kb_documents_bucket,
     module.vector_store
   ]
}

# ============================================================================
# Bedrock Data Source
# ============================================================================

resource "aws_bedrockagent_data_source" "s3_docs" {
  name              = "${var.project_name}-s3-docs-${var.environment}"
  knowledge_base_id = module.knowledge_base.knowledge_base_id

  data_deletion_policy = "DELETE"
  
  data_source_configuration {
    type = "S3"
    
    s3_configuration {
      bucket_arn = module.kb_documents_bucket.s3_bucket_arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "NONE"
      
      # fixed_size_chunking_configuration {
      #   max_tokens         = 300
      #   overlap_percentage = 20
      # }
    }
  }
}
