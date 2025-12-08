output "agent_runtime_id" {
  description = "AgentCore Runtime ID"
  value       = aws_bedrockagentcore_agent_runtime.agentcore_runtime.agent_runtime_id
}

output "agent_runtime_version" {
  description = "AgentCore Runtime Version"
  value       = aws_bedrockagentcore_agent_runtime.agentcore_runtime.agent_runtime_version
}

output "dev_endpoint_arn" {
  description = "DEV Endpoint ARN"
  value       = aws_bedrockagentcore_agent_runtime_endpoint.dev_endpoint.agent_runtime_endpoint_arn
}

output "execution_role_arn" {
  description = "Execution Role ARN"
  value       = aws_iam_role.agentcore_runtime_execution_role.arn
}
