variable "knowledge_base_name" {
  description = "Name of the knowledge base"
  type        = string
}

variable "description" {
  description = "Description of the knowledge base"
  type        = string
  default     = ""
}

variable "role_arn" {
  description = "ARN of the IAM role with permissions to invoke API operations on the knowledge base"
  type        = string
}

variable "embedding_model_arn" {
  description = "ARN of the model used to create vector embeddings for the knowledge base"
  type        = string
  default     = "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0"
}

variable "vector_bucket_arn" {
  description = "ARN of the S3 bucket where vector embeddings are stored"
  type        = string
}

variable "index_name" {
  description = "Name of the vector index used for the knowledge base"
  type        = string
}

variable "index_arn" {
  description = "ARN of the vector index used for the knowledge base"
  type        = string
}

variable "tags" {
  description = "Map of tags to assign to the knowledge base"
  type        = map(string)
  default     = {}
}
