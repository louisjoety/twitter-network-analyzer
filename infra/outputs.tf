output "app_config" {
  description = "JSON configuration accepted by the local backend. Contains no credentials."
  value = {
    region             = var.region
    bucket             = aws_s3_bucket.lab.id
    application_id     = aws_emrserverless_application.spark.id
    execution_role_arn = aws_iam_role.emr_job.arn
    input_key          = "input/twitter_combined.txt"
    script_key         = "scripts/analysis.py"
    output_prefix      = "output"
    logs_prefix        = "logs"
  }
}
