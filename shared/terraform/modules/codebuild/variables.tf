variable "name" {
    type = string
    description = "Name of the codebuild project"
}

variable "description" {
    type = string
    description = "Description of the codebuild project"
}

variable "image_repo_name" {
    type = string
    description = "Name of the image repository"
}

variable "image_tag" {
    type = string
    description = "Tag of the image"
}

variable "s3_source_location" {
    type = string
    description = "Location of the source code"
}

variable "s3_source_arn" {
    type = string
    description = "ARN of the source code"
}