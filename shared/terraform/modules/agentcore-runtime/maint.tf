data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

################################################################################
# AgentCore Runtime IAM Roles
################################################################################

data "aws_iam_policy_document" "bedrock_agentcore_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "agentcore_runtime_execution_role" {
  name        = "${title(var.agent_name)}-AgentCoreRuntimeRole"
  description = "Execution role for Bedrock AgentCore Runtime"

  assume_role_policy = data.aws_iam_policy_document.bedrock_agentcore_assume_role.json
}

# https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html#runtime-permissions-execution
resource "aws_iam_role_policy" "agentcore_runtime_execution_role_policy" {
  role   = aws_iam_role.agentcore_runtime_execution_role.id
  name = "${title(var.agent_name)}-AgentCoreRuntimeExecutionPolicy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRImageAccess"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = [
          "arn:aws:ecr:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:repository/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogStreams",
          "logs:CreateLogGroup",
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*",
        ]
      },
      {
        Sid    = "ECRTokenAccess"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
        ]
        Resource = [
          "*",
        ]
      },
      {
        Effect   = "Allow"
        Resource = "*"
        Action   = "cloudwatch:PutMetricData"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "bedrock-agentcore"
          }
        }
      },
      {
        Sid    = "GetAgentAccessToken"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:GetWorkloadAccessToken",
          "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
          "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
        ]
        Resource = [
          "arn:aws:bedrock-agentcore:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default",
          "arn:aws:bedrock-agentcore:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:workload-identity-directory/default/workload-identity/agentName-*",
        ]
      },
      {
        Sid    = "BedrockModelInvocation"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:*",
        ]
      },
      {
        Sid    = "MemoryAccess"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:ListEvents",
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:PutEvent",
          "bedrock-agentcore:DeleteEvent",
          "bedrock-agentcore:QueryMemory",
        ]
        Resource = [
          "arn:aws:bedrock-agentcore:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:memory/*",
        ]
      },
      {
        Sid    = "KnowledgeBaseAccess"
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate",
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:knowledge-base/*",
        ]
      },
    ]
  })
}
################################################################################
# AgentCore Memory
################################################################################
resource "aws_bedrockagentcore_memory" "agentcore_memory" {
  name                   = "${title(var.agent_name)}Memory"
  event_expiry_duration  = 30
}

################################################################################
# AgentCore Runtime
################################################################################
resource "aws_bedrockagentcore_agent_runtime" "agentcore_runtime" {
  agent_runtime_name = "${title(var.agent_name)}Runtime"
  role_arn           = aws_iam_role.agentcore_runtime_execution_role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${var.ecr_repository_url}:${var.image_tag}"
    }
  }

  depends_on = [aws_bedrockagentcore_memory.agentcore_memory]

  network_configuration {
    network_mode = "PUBLIC"
  }
  environment_variables = merge(
    {
      CODE_VERSION = var.src_hash
    },
    var.knowledge_base_id != "" ? {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
      MIN_SCORE         = "0.5"
    } : {}
  )
}


################################################################################
# AgentCore Runtime Endpoints
################################################################################
resource "aws_bedrockagentcore_agent_runtime_endpoint" "dev_endpoint" {
  name             = "DEV"
  agent_runtime_id = aws_bedrockagentcore_agent_runtime.agentcore_runtime.agent_runtime_id
  agent_runtime_version = aws_bedrockagentcore_agent_runtime.agentcore_runtime.agent_runtime_version
}
