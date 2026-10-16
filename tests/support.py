"""In-memory AWS doubles. These clients cannot send network requests."""

import csv
import io
import json
from pathlib import Path

from botocore.exceptions import ClientError
from botocore.session import get_session
from botocore.validate import validate_parameters

FIXTURES = Path(__file__).parent / "fixtures"
CONFIG = {
    "region": "ap-southeast-2", "bucket": "test-bucket", "application_id": "00testapplication",
    "execution_role_arn": "arn:aws:iam::123456789012:role/TestEmrJobRole",
    "input_key": "input/twitter_combined.txt", "script_key": "scripts/analysis.py",
    "output_prefix": "output", "logs_prefix": "logs",
}
METRICS = {"users": 5, "unique_edges": 6, "raw_lines": 10, "valid_edges": 7,
           "blank_lines": 1, "invalid_lines": 2, "duplicate_edges_removed": 1,
           "total_followers": 6, "total_followees": 6}


def fixture_rows():
    with (FIXTURES / "users.csv").open(newline="", encoding="utf-8") as stream:
        return [{"user_id": row["user_id"], "followers": int(row["followers"]),
                 "followees": int(row["followees"])} for row in csv.DictReader(stream)]


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.writes = []

    def get_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[Key])}

    def upload_file(self, filename, bucket, key):
        self.objects[key] = Path(filename).read_bytes()

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[Key] = Body
        self.writes.append(Key)

    def get_paginator(self, operation):
        if operation != "list_objects_v2":
            raise AssertionError(operation)
        return self

    def paginate(self, *, Bucket, Prefix):
        keys = sorted((key for key in self.objects if key.startswith(Prefix)), reverse=True)
        for start in range(0, len(keys), 2):
            yield {"Contents": [{"Key": key} for key in keys[start:start + 2]]}

    def add_output(self, prefix):
        self.objects[prefix + "/users/part-000.csv"] = (FIXTURES / "users.csv").read_bytes()
        self.objects[prefix + "/users/_SUCCESS"] = b""
        self.objects[prefix + "/metrics/part-000.json"] = json.dumps(METRICS).encode()


class FakeEMR:
    def __init__(self, s3, states=None):
        self.s3 = s3
        self.states = list(states or ["RUNNING", "SUCCESS"])
        self.cancelled = []
        self.submissions = []

    def start_job_run(self, **parameters):
        shape = get_session().get_service_model("emr-serverless").operation_model("StartJobRun").input_shape
        validate_parameters(parameters, shape)
        self.submissions.append(parameters)
        uri = parameters["jobDriver"]["sparkSubmit"]["entryPointArguments"][-1]
        self.s3.add_output(uri.removeprefix("s3://test-bucket/"))
        return {"jobRunId": "testjob123"}

    def get_job_run(self, **parameters):
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        if state == "INTERRUPT":
            raise KeyboardInterrupt()
        return {"jobRun": {"state": state, "stateDetails": "Test job failure"}}

    def cancel_job_run(self, **parameters):
        self.cancelled.append(parameters)


class FakeSession:
    def __init__(self, states=None):
        self.s3 = FakeS3()
        self.emr = FakeEMR(self.s3, states)
        self.client_requests = []

    def client(self, service):
        self.client_requests.append(service)
        return {"s3": self.s3, "emr-serverless": self.emr}[service]
