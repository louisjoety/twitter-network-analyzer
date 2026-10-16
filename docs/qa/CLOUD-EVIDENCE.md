# Cloud execution evidence

## Existing evidence

The recorded AWS EMR Serverless job is `00g9iqgvp7fp282b`, under application
`00g9iq66adh8au29` in Sydney (`ap-southeast-2`). It completed successfully on
16 October 2026. No new job is needed to inspect its history or S3 output.

- [Actual AWS console screenshot](evidence/emr-success.png): Success status, job ID
  and resource usage from the completed run. Original historical labels are
  preserved so this remains an authentic record.
- [Saved analysis metrics](evidence/cloud-run.json): Spark runtime, job/application
  IDs, timing and aggregate totals. This is supporting data, not a console screenshot.
- [Dashboard screenshots](../ux/README.md): display the real completed results;
  these demonstrate the application but do not independently prove cloud execution.

## Capture additional screenshots in AWS

Use the existing resources; do not select Run or Submit job.

| Screenshot | Where to find it | Include in the capture |
| --- | --- | --- |
| Completed analysis | EMR Serverless, open the application above, then its batch job history and the job above | Job ID, Success state, start/end times or duration; resource use if available |
| Stored result files | S3, bucket `twitter-combined-a0281523j`, prefix `output/runs/20261016T152205Z-a0724ea4/` | Bucket/prefix and the `users/` and `metrics/` output folders; open a folder to show its output objects |
| Spark driver output | Open the completed job's driver logs, or browse its job logs under the bucket's `logs/` prefix | Spark version, application startup and `ANALYSIS_COMPLETE` metrics if the logs are still retained |

The Spark script prints `ANALYSIS_COMPLETE` after writing output. If the console
logs link is unavailable, inspect the S3 log objects for this exact job ID. Do not
present a startup-only log as proof of successful completion; pair it with the
Success state and output objects. If resources/logs have been deleted, use the
retained evidence and state that the cloud resources were cleaned up.

Save additional captures in `docs/qa/evidence/` and link them here. Avoid including
credentials or sign-in information. There is currently one retained AWS-console
screenshot, not three independently captured cloud screenshots.

## What the analysis did

[compute_stats](../../analysis/job.py) reads the edge list, validates two numeric
IDs per line, removes repeated ordered `(src, dst)` pairs, groups destinations for
follower counts and sources for followee counts, and joins both sides with zero
for missing counts. `A B` means A follows B; `A B` and `B A` are different edges.

The same script starts Spark in its main block, writes `users/` CSV parts and
`metrics/` JSON, and prints the metrics. [Backend run_job](../../backend/app.py)
uploads that script to S3, submits it to EMR, waits for success, validates the
output and publishes `output/latest.json`. The small [Spark regression suite](../../tests/analysis/test_job.py)
checks the production counting function with hand-computed graphs.

Recorded totals: 2,426,143 valid input rows, 657,994 extra duplicate copies removed,
1,768,149 unique directed relationships and 81,306 users. Both follower and
followee totals equal the unique-edge count.

## Why the web app can run offline

EMR produced the data once and saved it in S3. The backend downloaded a copy into
`runtime/results.json`, which Docker reads through a read-only mount. Restarting
the web app, searching or paginating does not start Spark or submit an EMR job.
If the local copy is missing, load the existing S3 output using the profile command
in [setup](../setup.md). Only an explicit `--run-job` requests new computation.

Infrastructure details and run provenance remain in the health API, logs and
these technical documents. The customer dashboard shows counts and interactions;
it does not display the AWS service names, region or execution timestamp.
