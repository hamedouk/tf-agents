output "knowledge_base_id" {
  description = "Unique identifier of the knowledge base"
  value       = awscc_bedrock_knowledge_base.this.id
}

output "knowledge_base_arn" {
  description = "ARN of the knowledge base"
  value       = awscc_bedrock_knowledge_base.this.knowledge_base_arn
}

output "knowledge_base_name" {
  description = "Name of the knowledge base"
  value       = awscc_bedrock_knowledge_base.this.name
}

output "created_at" {
  description = "Time at which the knowledge base was created"
  value       = awscc_bedrock_knowledge_base.this.created_at
}

output "updated_at" {
  description = "Time at which the knowledge base was last updated"
  value       = awscc_bedrock_knowledge_base.this.updated_at
}
