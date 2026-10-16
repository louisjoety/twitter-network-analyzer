# BDD specs: twitter-network-analyzer

Status: behavior examples backed by existing executable regression tests.

The Given/When/Then examples below describe observable behavior. Their executable
backing is the mapped Python unittest suite; this repository does not install a
separate Gherkin/Cucumber parser. Fixtures are synthetic and AWS clients are fake.

```gherkin
Feature: Trustworthy network counts
  Scenario: Repeated relationships count once
    Given the relationship 100 follows 200 appears three times
    When the network is analysed
    Then 100 has one followee and 200 has one follower
    And two extra duplicate copies are removed

  Scenario: Look up an existing user
    Given the sample network results are loaded
    When I request user 200
    Then I receive 2 followers and 2 followees

  Scenario: Reject an invalid user ID
    Given the results are loaded
    When I request the user ID abc
    Then I receive HTTP 400

  Scenario: Reuse saved results offline
    Given a local result cache exists and AWS access is blocked
    When I start the application offline
    Then cached counts are served without accessing AWS

  Scenario: Keep the last successful result after a failed job
    Given a successful result pointer already exists
    When a new analysis fails or is cancelled
    Then the successful pointer is preserved
```

| Scenario | Executable backing |
| --- | --- |
| Repeated relationships | `AnalysisTests.test_duplicate_pairs_keep_one_relationship` in [test_job.py](../../tests/analysis/test_job.py) |
| Existing user | `ApiTests.test_user_lookup_returns_follower_and_followee_counts` in [test_api.py](../../tests/backend/test_api.py) |
| Invalid ID | `ApiTests.test_invalid_user_ids_return_400` in [test_api.py](../../tests/backend/test_api.py) |
| Offline reuse | `StartupTests.test_offline_mode_reads_cache_without_aws` in [test_startup.py](../../tests/backend/test_startup.py) |
| Failed/cancelled job | `OrchestrationTests.test_failed_or_cancelled_job_preserves_previous_pointer` in [test_orchestration.py](../../tests/backend/test_orchestration.py) |

Run from the repository root after installing the prerequisites in the [QA plan](README.md):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests/backend -v
.\.venv\Scripts\python.exe -m unittest discover -s tests/analysis -v
```

The analysis suite additionally needs Java/PySpark; it runs locally on tiny graphs
and in the existing Linux CI job. No scenario submits a real EMR job.
