output "s3_bucket_object_key" {
  value = aws_s3_object.source.key
}

output "s3_bucket_object_hash" {
  value = aws_s3_object.source.etag
}

