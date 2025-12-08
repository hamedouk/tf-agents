output "project_name" {
  value = aws_codebuild_project.build_project.name
  description = "The name of the CodeBuild project"
}

output "image_tag" {
  value = var.image_tag
  description = "The Docker image tag used by CodeBuild"
}
