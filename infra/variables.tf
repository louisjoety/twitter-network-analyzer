variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "bucket_name" {
  type        = string
  description = "Existing project bucket, or a globally unique name for a new deployment."
}

variable "role_name" {
  type    = string
  default = "twitter-combined-a0281523j-emr-role"
}

variable "role_description" {
  type    = string
  default = "twitter-network-analyzer EMR execution role"
}

variable "policy_name" {
  type    = string
  default = "twitter-combined-access"
}

variable "application_name" {
  type    = string
  default = "twitter-combined-emr"
}

variable "release_label" {
  type    = string
  default = "emr-spark-8.0.0"
}
