locals {
  agent_name = "supervisor"
}
module "s3" {
  source = "../../../shared/terraform/modules/s3"
  s3_bucket_prefix = "tf-agents-code-src-"
}

module code_upload {
  source = "../../../shared/terraform/modules/s3-upload"
  bucket_id = module.s3.s3_bucket_id
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
    s3_source_location =  "${module.s3.s3_bucket_id}/${module.code_upload.s3_bucket_object_key}"
    s3_source_arn =  module.s3.s3_bucket_arn

    depends_on = [
     module.s3,
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
    
    depends_on = [
      null_resource.trigger_build_agent
    ]
}