locals {
  agent_name = "supervisor"
}

# Reference shared infrastructure
data "terraform_remote_state" "shared" {
  backend = "s3"
  config = {
    bucket  = "tfagents-terraform-state-730335657558"
    key     = "tfagents/shared/infrastructure/terraform.tfstate"
    region  = "us-west-2"
    profile = "ai"
  }
}

module code_upload {
  source = "../../../shared/terraform/modules/s3-upload"
  bucket_id = data.terraform_remote_state.shared.outputs.agents_code_bucket_id
  agent_name = local.agent_name
  code_path = "${path.module}/../code/"
}

module "agent_ecr" {
  source = "../../../shared/terraform/modules/ecr-repo"
  name = "${local.agent_name}-agent"
}

module "codebuild" {
    source = "../../../shared/terraform/modules/codebuild"
    name = local.agent_name
    description = "Codebuild project for the ${local.agent_name} agent"
    image_repo_name = module.agent_ecr.image_repo_name
    image_tag = "latest"
    s3_source_location =  "${data.terraform_remote_state.shared.outputs.agents_code_bucket_id}/${module.code_upload.s3_bucket_object_key}"
    s3_source_arn =  data.terraform_remote_state.shared.outputs.agents_code_bucket_arn

    depends_on = [
     module.code_upload,
     module.agent_ecr
    ]
  
}

# Trigger Agent Build
resource "null_resource" "trigger_build_agent" {
  triggers = {
    build_project   = module.codebuild.project_name
    image_tag       = module.codebuild.image_tag
    ecr_repository  = module.agent_ecr.image_repo_name
    source_code_md5 = module.code_upload.s3_bucket_object_hash
  }

  provisioner "local-exec" {
    command = "AWS_PROFILE=${var.aws_profile} bash ${path.module}/../../../shared/scripts/build-images.sh \"${module.codebuild.project_name}\" \"${data.aws_region.current.id}\" \"${module.agent_ecr.image_repo_name}\" \"${module.codebuild.image_tag}\" \"${module.agent_ecr.image_repo_url}\""
  }
  
  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Build trigger removed'"
  }

  depends_on = [
    module.codebuild,
    module.agent_ecr,
    module.code_upload
  ]
}

module "agentcore_runtime" {
    source = "../../../shared/terraform/modules/agentcore-runtime"
    agent_name = local.agent_name
    src_hash = module.code_upload.s3_bucket_object_hash
    ecr_repository_url = module.agent_ecr.image_repo_url
    image_tag = module.codebuild.image_tag
    knowledge_base_id = data.terraform_remote_state.shared.outputs.knowledge_base_id
    
    depends_on = [
      null_resource.trigger_build_agent
    ]
}