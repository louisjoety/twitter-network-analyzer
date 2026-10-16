# Product requirements: twitter-network-analyzer

Status: implemented prototype. Updated: 17 October 2026.

## Problem and objective

The supplied Twitter edge list contains repeated directed relationships. A user
needs correct follower/followee totals and a simple way to inspect them, backed
by evidence that the analysis actually ran in AWS.

The product processes a fixed dataset in EMR Serverless, stores results in S3,
and presents them through a local React/FastAPI application. Subsequent viewing
can reuse saved results without submitting another analysis job.

## Users and journeys

- Analyst: configure input, explicitly run an analysis, inspect the two featured
  users, search another ID and record the analysis results.
- Reviewer: inspect screenshots, source, architecture and reproducible test cases.
- Developer: run a clearly labelled sample, test changes and build the container.

## Functional requirements and acceptance

| ID | Requirement | Acceptance criterion | Evidence |
| --- | --- | --- | --- |
| FR-01 | Interpret `src dst` as src following dst | Src gains a followee; dst gains a follower | Analysis cases AN-01, AN-03 |
| FR-02 | Count each distinct directed pair once | Repeated pairs collapse; different neighbors and reciprocal pairs survive | AN-02, AN-03 |
| FR-03 | Include one-sided users | Missing follower/followee count is zero, not an omitted user | AN-04, API-03 |
| FR-04 | Display required IDs 214328887 and 107830991 | Both cards show API-provided follower and followee statements | FE-01; real cloud screenshots |
| FR-05 | Support ID lookup and browsing | Numeric lookup, useful unknown-ID errors, stable page boundaries | FE-03 to FE-07; API-04 to API-08 |
| FR-06 | Coordinate real cloud analysis | Read S3 input, submit Spark to EMR and publish validated output after success | JOB-01 to JOB-08; cloud-run evidence |
| FR-07 | Reuse completed results safely | Saved S3 reads do not submit jobs; offline/demo modes do not access AWS | JOB-07; MODE-01 to MODE-04 |
| FR-08 | Support both themes and a clear sample warning | Accessible theme control; persisted preference; sample data labelled; run provenance available in the health API | FE-09 to FE-13; UX screenshots |

## Quality requirements

- Correctness: reject malformed records, deduplicate ordered pairs, preserve exact
  string IDs and verify both degree sums against the unique-edge count.
- Failure handling: incomplete/corrupt output must not replace a successful result
  pointer; unfinished jobs are cancelled on interrupt, polling failure or timeout.
- Usability: readable desktop/narrow layouts, labelled search, keyboard-operable
  controls, loading indicators and useful errors.
- Reproducibility: pinned dependency lockfiles, small deterministic tests,
  container build, infrastructure code and documented setup.
- Access: private S3 bucket, bucket-scoped runtime permissions and local credential
  resolution. Bind the web app to localhost in the current deployment.

## Scope boundaries

Included: batch analytics, S3/EMR integration, API, search, pagination, themes,
offline reuse, Docker, infrastructure definitions and CI/manual image publishing.

Deferred: public hosting, authentication, live Twitter ingestion, arbitrary uploads,
social-network visualisation, RDS and automatic AWS deployment. Fargate or EC2 can
host a later container deployment after its network/access design is added.

## Release acceptance

The automated suites, frontend build/lint, infrastructure validation and Docker
smoke check must pass. The recorded cloud output contains 81,306 users and
1,768,149 distinct relationships. Required results are 180/214 and 180/157
(followers/followees respectively). Manual/browser evidence must be labelled
separately from automated tests; see [QA](../qa/README.md).
