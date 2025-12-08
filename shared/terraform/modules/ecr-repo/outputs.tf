output "image_repo_name" {
    value = aws_ecr_repository.agentcore_terraform_runtime.name
    description = "The name of the ECR repository"
}

output "image_repo_url" {
    value = aws_ecr_repository.agentcore_terraform_runtime.repository_url
    description = "The URL of the ECR repository"
}
  