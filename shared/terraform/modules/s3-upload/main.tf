# ============================================================================
# Archive and Upload Agent Source Code
# ============================================================================

# Archive agent-orchestrator-code/ directory
data "archive_file" "source" {
  type        = "zip"
  source_dir  = var.code_path
  output_path = "${path.module}/.terraform/agent-${var.agent_name}-code.zip"
}

# Upload Orchestrator source to S3
resource "aws_s3_object" "source" {
  bucket = var.bucket_id
  key    = "agent-${var.agent_name}-code-${data.archive_file.source.output_md5}.zip"
  source = data.archive_file.source.output_path
  etag   = data.archive_file.source.output_md5

  tags = {
    Name  = "agent-${var.agent_name}-source-code"
    Agent = "${title(var.agent_name)}"
    MD5   = data.archive_file.source.output_md5
  }
}