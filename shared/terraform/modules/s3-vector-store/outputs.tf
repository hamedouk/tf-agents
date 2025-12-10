output "vector_bucket_arn" {
  description = "ARN of the vector bucket"
  value       = awscc_s3vectors_vector_bucket.this.vector_bucket_arn
}

output "vector_bucket_name" {
  description = "Name of the vector bucket"
  value       = awscc_s3vectors_vector_bucket.this.vector_bucket_name
}

output "index_arn" {
  description = "ARN of the vector index"
  value       = awscc_s3vectors_index.this.index_arn
}

output "index_name" {
  description = "Name of the vector index"
  value       = awscc_s3vectors_index.this.index_name
}

output "creation_time" {
  description = "Creation time of the vector bucket"
  value       = awscc_s3vectors_vector_bucket.this.creation_time
}
