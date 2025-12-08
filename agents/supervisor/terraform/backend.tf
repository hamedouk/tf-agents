terraform {
  backend "s3" {
    bucket         = "tfagents-terraform-state-730335657558"
    key            = "tfagents/supervisor/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    use_lockfile   = true
    profile        = "ai"
  }
}
