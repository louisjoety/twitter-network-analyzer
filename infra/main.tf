data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "lab" {
  bucket        = var.bucket_name
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_role" "emr_job" {
  name        = var.role_name
  description = var.role_description
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "emr-serverless.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = { StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id } }
    }]
  })
}

resource "aws_iam_role_policy" "s3" {
  name = var.policy_name
  role = aws_iam_role.emr_job.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InspectLabBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetBucketLocation", "s3:ListBucketMultipartUploads"]
        Resource = aws_s3_bucket.lab.arn
      },
      {
        Sid      = "ReadDatasetAndScript"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = ["${aws_s3_bucket.lab.arn}/input/*", "${aws_s3_bucket.lab.arn}/scripts/*"]
      },
      {
        Sid      = "WriteResultsAndLogs"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
        Resource = ["${aws_s3_bucket.lab.arn}/output/*", "${aws_s3_bucket.lab.arn}/logs/*"]
      }
    ]
  })
}

resource "aws_emrserverless_application" "spark" {
  name          = var.application_name
  release_label = var.release_label
  type          = "spark"
  architecture  = "X86_64"

  maximum_capacity {
    cpu    = "4 vCPU"
    memory = "24 GB"
    disk   = "60 GB"
  }

  # Omitted initial_capacity means no pre-initialized workers.
  auto_start_configuration {
    enabled = true
  }
  auto_stop_configuration {
    enabled              = true
    idle_timeout_minutes = 15
  }
  interactive_configuration {
    studio_enabled        = false
    livy_endpoint_enabled = false
  }
}
