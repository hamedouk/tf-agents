output "agent_runtime_id" {
  description = "AgentCore Runtime ID"
  value       = module.agentcore_runtime.agent_runtime_id
}

output "dev_endpoint_arn" {
  description = "DEV Endpoint ARN"
  value       = module.agentcore_runtime.dev_endpoint_arn
}

output "ecr_repository_url" {
  description = "ECR Repository URL"
  value       = module.agent_ecr.image_repo_url
}

output "codebuild_project_name" {
  description = "CodeBuild Project Name"
  value       = module.codebuild.project_name
}
