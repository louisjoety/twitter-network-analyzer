# Test cases and expected outcomes

Each automated case below maps to a named test. Multi-value cases use subtests.
Fixtures use synthetic IDs; real required-user counts are checked in the archived
cloud/browser evidence rather than hard-coded into production logic.

## API: `tests/backend/test_api.py`

| ID | Input/action | Expected outcome |
| --- | --- | --- |
| API-01 | Request health for loaded fixture | Ready, user total and job provenance returned |
| API-02 | Look up fixture user 200 | Two followers and two followees |
| API-03 | Look up one-sided users 400 and 500 | Zero follower/followee value retained |
| API-04 | Look up absent numeric ID 999 | 404 |
| API-05 | Look up abc, -1, 1.5 and non-ASCII digits | 400 for each |
| API-06 | Fetch two adjacent two-user pages | Stable order, no overlap and same total |
| API-07 | Fetch offset beyond result length | Empty items, successful response |
| API-08 | Limit 0/201, negative or nonnumeric offset | 422 |
| API-09 | Provide a built index and JS asset | Homepage and asset return 200 |
| API-10 | Omit frontend build | 503 with build instructions |

## Aggregate integrity: `tests/backend/test_results.py`

| ID | Input/action | Expected outcome |
| --- | --- | --- |
| DATA-01 | Split CSV across S3 parts and listing pages; include unrelated file | All five fixture users loaded once; unrelated file ignored |
| DATA-02 | Remove CSV output | Incomplete-output error |
| DATA-03 | Supply multiple metrics parts | Ambiguous/incomplete-output error |
| DATA-04 | Change required CSV column names | Schema error |
| DATA-05 | Duplicate a user while preserving row count | Reject duplicate IDs |
| DATA-06 | Corrupt either degree total | Reject mismatched followers/followees sum |
| DATA-07 | Introduce negative counts while balancing the global sum | Reject negative values |
| DATA-08 | Supply a nonnumeric result ID | Reject invalid ID |
| DATA-09 | Read saved results before a pointer exists | Actionable first-run error |

## Job orchestration: `tests/backend/test_orchestration.py`

| ID | Input/action | Expected outcome |
| --- | --- | --- |
| JOB-01 | Simulate running then success | Valid request uses S3 script; validated results published; no local master |
| JOB-02 | Simulate FAILED/CANCELLED terminal state | Previous pointer preserved; no redundant cancellation |
| JOB-03 | Interrupt a running job | Cancel once; do not publish results |
| JOB-04 | Fail job-status polling | Cancel unfinished job |
| JOB-05 | Exceed local wait deadline | Timeout and cancellation |
| JOB-06 | Successful job produces invalid output | Reject output; do not publish pointer |
| JOB-07 | Load saved results | Use S3 only; create no EMR client |
| JOB-08 | Run two explicit submissions | Different prefixes; first run's parts preserved |

## Startup/configuration: `tests/backend/test_startup.py`

| ID | Input/action | Expected outcome |
| --- | --- | --- |
| MODE-01 | Start offline with fixture cache and AWS blocked | Serve cached counts with offline metadata in the health API; no AWS access |
| MODE-02 | Start offline without cache | Exit 1; no AWS access |
| MODE-03 | Start demo with AWS blocked | Serve labelled sample data |
| MODE-04 | Combine --offline and --run-job | Argument error; exit 2 |
| MODE-05 | Start normally with config/local.json and saved S3 output, using fake clients | Read S3 only, submit no job and create runtime/results.json for offline reuse |
| CFG-01 | Use placeholder application ID | Reject configuration |
| CFG-02 | Use /output/ as prefix | Normalize to output |

## Production Spark algorithm: `tests/analysis/test_job.py`

| ID | Graph/input | Expected outcome |
| --- | --- | --- |
| AN-01 | 100 -> 200 | 100: 0 followers/1 followee; 200: 1/0 |
| AN-02 | Repeat 100 -> 200 three times | One edge, two extra copies removed |
| AN-03 | 100 -> 200, 200 -> 100, 100 -> 300 | Keep all three distinct directed edges |
| AN-04 | Two sources pointing to 200 | Sources retain zero followers; 200 retains zero followees |
| AN-05 | Repeat self-loop 100 -> 100 | One follower and one followee for 100 |
| AN-06 | Tabs/spaces, blank line, malformed records | Valid relationship retained; blank/invalid metrics correct |
| AN-07 | No valid relationships | Fail rather than publish an empty analysis |
| AN-08 | ID larger than a 64-bit integer | Preserve exact string; both degree sums equal one |

## Frontend: named FE cases in `frontend/src/**/*.test.tsx`

| ID | Action/setup | Expected outcome |
| --- | --- | --- |
| FE-01 | Load API responses for both required IDs | Correct follower/followee statements in both cards |
| FE-02 | Load health totals | Dataset summary displays returned values |
| FE-03 | Search numeric ID with a response | Search card shows returned counts |
| FE-04 | Search abc | Inline validation; no request for that ID |
| FE-05 | Search absent numeric ID | Show backend's unknown-user message |
| FE-06 | Navigate to final page and back | Correct rows and boundary button states |
| FE-07 | Next-page request fails | Show error and retain previous page |
| FE-08 | Health request fails | Show useful backend error |
| FE-09 | Load demo metadata | Explicit sample-data warning |
| FE-10 | Load offline metadata | Correct counts with no infrastructure badge, region or run timestamp |
| FE-11 | Toggle both themes | Root class and stored preference update |
| FE-12 | Activate theme button by keyboard | Theme changes |
| FE-13 | Block browser storage and toggle | Control still works |

## Browser, container and cloud acceptance

| ID | Steps | Expected outcome | Method |
| --- | --- | --- | --- |
| UX-01 | Open real result page in both themes | Readable cards/table with both required users | Browser/screenshots |
| UX-02 | Choose theme, reload | Choice persists; no data changes | Browser |
| UX-03 | Inspect 375px and desktop layouts; search and page | No page overflow; controls usable | Browser, release check |
| PKG-01 | Build image and run --demo | Homepage and known sample API response succeed | CI Docker smoke check |
| PKG-02 | Start Compose with real cache | Healthy offline app; required counts match evidence | Local Docker acceptance |
| INF-01 | fmt, init without backend, validate | Valid schema; no AWS deployment | Terraform |
| CLOUD-01 | Inspect archived successful EMR job and metrics | Job succeeded; real counts/totals match screenshots | Existing cloud evidence |

Use [execution results](TEST-RESULTS.md) for actual pass/pending status. Writing a
test case does not mean its browser/platform scenario has been executed.
