# Infrastructure: S3 and EMR Serverless

From the repository root, enter this folder with `Set-Location infra`.

This configuration describes the project bucket, its private-access/encryption settings,
the EMR runtime role and inline S3 policy, and the small EMR Serverless application.
State stays on your computer. There is no web hosting or database in this plan.
The existing console-only EMR Studio is left unmanaged; batch submissions use the
EMR Serverless application directly.

The project resources were created manually. Import them before asking Terraform to
manage them. The validation checks below do not change AWS resources.

## Validate files without contacting your AWS account

Install [Terraform](https://developer.hashicorp.com/terraform/install). From this
folder, run:

```powershell
terraform fmt -check
terraform init -backend=false -input=false
terraform validate
```

Initialization downloads the provider from its public registry. These checks do
not create resources or submit an EMR job. Commit `.terraform.lock.hcl` with the
source; keep `.terraform/`, state, plans and local variable values out of Git.

## Adopt your existing resources, only if you want Terraform to manage them

Do this before any apply against the existing account. Without imports, Terraform
would try to create resources instead of adopting the manually created ones.
Do not use these import commands after you have deleted the project resources.

1. Copy the example values and sign in locally. Replace `your-profile` with your
   existing AWS CLI profile name:

   ```powershell
   Copy-Item -LiteralPath terraform.tfvars.example -Destination terraform.tfvars
   aws login --profile your-profile --region ap-southeast-2
   $env:AWS_PROFILE = 'your-profile'
   terraform init
   ```

2. Import the existing resources into local state:

   ```powershell
   terraform import aws_s3_bucket.lab twitter-combined-a0281523j
   terraform import aws_s3_bucket_public_access_block.lab twitter-combined-a0281523j
   terraform import aws_s3_bucket_ownership_controls.lab twitter-combined-a0281523j
   terraform import aws_s3_bucket_server_side_encryption_configuration.lab twitter-combined-a0281523j
   terraform import aws_iam_role.emr_job twitter-combined-a0281523j-emr-role
   terraform import aws_iam_role_policy.s3 twitter-combined-a0281523j-emr-role:twitter-combined-access
   terraform import aws_emrserverless_application.spark 00g9iq66adh8au29
   ```

   These imports read AWS resources and write local state. Keep state private.
   They do not run the analysis or upload the dataset.

3. Review the proposed changes:

   ```powershell
   terraform plan -out=project.tfplan
   ```

   Check all differences against your actual console settings. Do not apply a
   plan that would recreate an existing resource or change settings you need.
   `prevent_destroy` protects the bucket from Terraform deletion; `force_destroy`
   is false, so Terraform will not empty it. These guards do not affect manual
   deletions in the AWS console.

4. Only after deliberately choosing to make the reviewed changes:

   ```powershell
   terraform apply project.tfplan
   terraform output -json app_config | Set-Content -Encoding utf8 ../config/local.json
   ```

   No apply is necessary to keep using the already completed analysis results.

## Create a fresh setup later

Use a fresh state directory and edit the example values: choose a unique bucket
name and different role/application names. Run `init`, review `plan`, then apply
only if you intend to create those resources. Upload the dataset separately;
Terraform does not manage the raw data, results, job runs or logs as objects.
The role only permits access to this bucket's input, script, output and logs.

The application has no pre-initialized workers, a 4-vCPU/24-GB/60-GB maximum,
automatic start on job submission and automatic stop after 15 idle minutes.
Those are resource limits, not a monetary spending limit. Any new analysis is
submitted separately using the app's explicit `--run-job` option.

Do not apply this configuration after intentionally cleaning up the project unless
you want to recreate its resources. No Terraform deployment runs in CI.

## Manual console setup

`policies/` retains the trust and S3 policy JSON used for the manual project setup.
Review the account and bucket identifiers before reuse. Terraform builds the
equivalent policies from variables and the current account. For a manually
created application, copy the template `../config/example.json` to private
`../config/local.json`, fill in the resource IDs, and authenticate with your existing
CLI profile. Runtime configuration and Terraform state are not committed.
