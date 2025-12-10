# Shared Infrastructure

This directory contains shared resources used by all agents:

## Resources

- **S3 Bucket**: Single bucket for all agent source code (organized by agent name)
- **S3 Vector Store**: Vector storage for knowledge base embeddings
- **Bedrock Knowledge Base**: Shared knowledge base accessible by all agents

## Deployment Order

1. Deploy shared infrastructure first:
   ```bash
   cd shared/terraform/infrastructure
   terraform init
   terraform apply
   ```

2. Deploy individual agents (they reference shared infrastructure via remote state):
   ```bash
   cd agents/supervisor/terraform
   terraform init
   terraform apply
   ```

## Outputs

Agents reference these outputs via `terraform_remote_state`:
- `agents_code_bucket_id` - S3 bucket for agent code
- `agents_code_bucket_arn` - S3 bucket ARN
- `vector_bucket_arn` - Vector store bucket ARN
- `vector_index_name` - Vector index name
- `vector_index_arn` - Vector index ARN
- `knowledge_base_id` - Knowledge base ID
- `knowledge_base_arn` - Knowledge base ARN
