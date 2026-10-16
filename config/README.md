# Application configuration

`example.json` is a committed template containing placeholders. `local.json`
contains this computer's actual resource identifiers and is ignored by Git.
Neither file should contain passwords, access keys or session tokens. AWS
credentials come from your locally authenticated CLI profile.

From the repository root, create a local configuration on a new clone:

```powershell
Copy-Item -LiteralPath config/example.json -Destination config/local.json
```

Fill in the region, bucket, EMR application ID and execution role ARN. Keep the
input/script/output/log prefixes aligned with the existing S3 objects and IAM
policy. Do not overwrite an already configured `local.json` just to run the app.

The default configuration path is `config/local.json`, resolved relative to the
project location, independently of the shell's working directory. An explicit
`--config <path>` selects another file. Configuration is read when loading saved
S3 results or intentionally submitting a job. `--demo` and `--offline` do not need
configuration or AWS credentials.

Docker Compose uses the local result cache instead of AWS and therefore does not
mount this folder. The image excludes configuration and credentials.
