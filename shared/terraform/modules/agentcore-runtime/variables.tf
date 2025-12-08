variable "agent_name" {
    description = "Name of the agent"
    type = string
}

variable "src_hash" {
    description = "Source hash"
    type = string
}

variable "ecr_repository_url" {
    description = "ECR repository URL"
    type = string
}

variable "image_tag" {
    description = "Docker image tag"
    type = string
    default = "latest"
}
