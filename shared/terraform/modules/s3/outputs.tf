output "s3_bucket_arn" {
  value = aws_s3_bucket.source.arn
}

output "s3_bucket_id" {
  value = aws_s3_bucket.source.id
}
