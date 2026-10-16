# Test execution record

Date: 17 October 2026. Scope: GitHub-ready original project after reorganisation.

## Automated checks

| Check | Result | Scope |
| --- | --- | --- |
| Backend regression suite | 34 passed | API, aggregate integrity, orchestration, configuration and startup |
| Spark regression suite | 8 passed | Real Spark 4.0.1, tiny hand-computed graphs; not a full-dataset checker |
| React component suite | 13 passed | Vitest 5.0.5, Testing Library, jsdom; mocked HTTP |
| Frontend production build | Passed | TypeScript and Vite |
| Frontend lint | Passed | Oxlint |
| Infrastructure validation | Passed | Terraform fmt/validate against AWS provider 6.69.1 |
| Docker build and real-cache startup | Passed after reorganisation | Linux container; localhost only |

The automated suite contains 55 named tests, with additional parameterized
subcases. Windows Spark prints native-Hadoop/socket warnings; the suite completed
with `OK` and exit code zero. Backend tests intentionally exercise failure paths,
so expected error messages can appear in a passing run.

## Folder layout follow-up

After moving documentation into `docs/`, settings into `config/`, dependencies
into `requirements/` and private results from `work/` to `runtime/`:

- Re-ran all 34 backend tests, including MODE-05: normal startup reads the default
  configuration, loads the saved S3 result through fake clients, submits no job
  and writes a cache for offline reuse.
- Checked native offline startup with AWS blocked and the actual saved results;
  the homepage and both required-user counts passed.
- Rebuilt Docker and recreated Compose. Health, both required-user counts and
  the read-only `/app/runtime` mount passed. A temporary demo container passed
  homepage/sample-count checks and contained no private config, credentials or
  real cache; it was removed after verification.
- Resolved all 45 local Markdown link targets and checked that the moved
  configuration/cache files are byte-for-byte unchanged. All 69 recorded
  source/artifact hashes in the separate verification copy remained unchanged.
- Checked the development dependency include with pip's offline dry run. No
  dependency version was changed.

The eight Spark and thirteen frontend tests, frontend build/lint, Terraform
validation and browser checks below were completed earlier in this cleanup.
Their source was unchanged by this folder-only follow-up; they were not rerun.
The GitHub CI dependency paths and Docker paths now use the new layout.

## Project branding follow-up

Renamed the public project references to `twitter-network-analyzer` and linked
the GitHub repository from the root README. Course wording was removed from the
current documentation, dashboard, HTML metadata, API title and future job labels.
Existing AWS resource identifiers and historical cloud-run evidence were retained.

Re-ran 34 backend tests and 13 frontend tests; all passed. Frontend lint and
production build passed. Docker rebuilt successfully using the updated npm
package metadata, and the dashboard/browser title showed the project name.
Desktop (1280px) and mobile (375px) layouts had no horizontal page overflow.
Refreshed light, dark and mobile UX screenshots using the same real saved output;
no EMR job was submitted. The Spark algorithm itself was unchanged.

## Customer dashboard follow-up

Removed the cloud-status badge and region/execution timestamp from the customer
page. The sample-data warning remains; infrastructure provenance is available in
the health API and technical documents. Updated FE-09/FE-10 and acceptance criteria.
All 13 frontend tests, lint and the production build passed again. Rebuilt Docker
and checked the real saved counts, desktop/mobile layout and both themes. Updated
all three UX screenshots; no horizontal overflow at 1280px or 375px was observed.
Backend and Spark code were unchanged and their suites were not rerun for this UI
change. Added a cloud-evidence/source guide and moved detailed setup out of the
short root README. No new EMR job was submitted.

## Browser evidence

Light/dark rendering, required-user values, search and theme persistence across
reloads were checked in the browser during preparation. Screenshots are in
[`ux/screenshots/`](../ux/screenshots/). Those captures use the actual completed
cloud output. The rebuilt Docker app was checked at 1280x900 and a 375px narrow viewport during the earlier checks; the refreshed
branding captures use a 1280x720 desktop viewport and a 375x812 mobile viewport.
No horizontal page overflow was found; real user 12 returned 465 followers and
154 followees, and Next/Previous navigation worked. Light-theme preference
survived refresh. These are checks in the in-app browser, not a cross-browser matrix.

## Actual cloud run, retained as evidence

The EMR job completed on 16 October 2026. This cleanup/test run submitted no new
cloud job and applied no infrastructure changes.

- Job: `00g9iqgvp7fp282b`; Spark: `4.0.2-amzn-0`; master: `custom:emr-serverless`.
- Input: 2,426,143 rows; zero blank or invalid rows.
- Extra duplicate copies removed: 657,994; unique directed edges: 1,768,149.
- Users: 81,306; both degree sums: 1,768,149.
- Required users: 214328887 has 180 followers/214 followees;
  107830991 has 180 followers/157 followees.

Evidence: [job screenshot](evidence/emr-success.png),
[saved metrics](evidence/cloud-run.json), and the UX screenshots.

Fresh-clone demo Docker smoke check also passed: homepage 200 and fixture user
200 returned 2 followers/2 followees. The temporary test container was removed.
The real-cache Compose container remains healthy on port 8002.

## Documentation follow-up

Added brief BRD, draft hosting RFC, SDD, TSD and behavior specs, linked from the
documentation index. All local Markdown links resolve. Verified all five BDD
scenario mappings against the existing test methods and reran the four mapped
backend tests successfully. The mapped Spark duplicate test was already covered
by the earlier eight-test Spark run; it was not rerun for this documentation-only
change. The root README remains 32 lines; no application or deployment code changed.

## Limits

GitHub workflows have been prepared but not executed on GitHub. No new cloud
integration, public hosting, database, load testing, formal accessibility audit
or cross-browser matrix is claimed. Keep those distinctions when using this
record in a project report.
