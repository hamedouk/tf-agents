# ============================================================================
# Outputs for Agent Terraform to Reference
# ============================================================================

# S3 Bucket Outputs
output "agents_code_bucket_id" {
  description = "ID of the shared S3 bucket for agent source code"
  value       = module.agents_code_bucket.s3_bucket_id
}

output "agents_code_bucket_arn" {
  description = "ARN of the shared S3 bucket for agent source code"
  value       = module.agents_code_bucket.s3_bucket_arn
}

output "kb_documents_bucket_id" {
  description = "ID of the shared S3 bucket for knowledge base documents"
  value       = module.kb_documents_bucket.s3_bucket_id
}

output "kb_documents_bucket_arn" {
  description = "ARN of the shared S3 bucket for knowledge base documents"
  value       = module.kb_documents_bucket.s3_bucket_arn
}

# Vector Store Outputs
output "vector_bucket_arn" {
  description = "ARN of the S3 vector bucket"
  value       = module.vector_store.vector_bucket_arn
}

output "vector_index_name" {
  description = "Name of the vector index"
  value       = module.vector_store.index_name
}

output "vector_index_arn" {
  description = "ARN of the vector index"
  value       = module.vector_store.index_arn
}

# Knowledge Base Outputs
output "knowledge_base_id" {
  description = "ID of the shared knowledge base"
  value       = module.knowledge_base.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "ARN of the shared knowledge base"
  value       = module.knowledge_base.knowledge_base_arn
}

output "data_source_id" {
  description = "ID of the knowledge base data source"
  value       = aws_bedrockagent_data_source.s3_docs.data_source_id
}
