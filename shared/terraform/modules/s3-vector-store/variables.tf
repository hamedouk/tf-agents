variable "vector_bucket_name" {
  description = "Name of the vector bucket"
  type        = string
}

variable "sse_type" {
  description = "Server-side encryption type (AES256 or aws:kms)"
  type        = string
  default     = "AES256"
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption (required if sse_type is aws:kms)"
  type        = string
  default     = null
}

variable "index_name" {
  description = "Name of the vector index"
  type        = string
}

variable "dimension" {
  description = "Dimensions of the vectors (e.g., 1024 for titan-embed-text-v2)"
  type        = number
}

variable "data_type" {
  description = "Data type of the vectors (FLOAT32 or BINARY)"
  type        = string
  default     = "FLOAT32"
}

variable "distance_metric" {
  description = "Distance metric for similarity search (COSINE, EUCLIDEAN, or DOT_PRODUCT)"
  type        = string
  default     = "COSINE"
}

variable "non_filterable_metadata_keys" {
  description = "Non-filterable metadata keys for enriching vectors"
  type        = list(string)
  default     = null
}

variable "kb_role_arn" {
  description = "Role ARN of the knowledge base"
  type = string
}
