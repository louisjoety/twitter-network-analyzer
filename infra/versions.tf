terraform {
  required_version = ">= 1.5, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # Default local state: terraform.tfstate. No remote backend is created.
}

provider "aws" {
  region = var.region
}
