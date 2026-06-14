"""The published envelope JSON Schema validates envelopes (language-agnostic)."""

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).parent.parent.parent / "docs" / "contracts" / "event-envelope.schema.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_file_published() -> None:
    assert SCHEMA_PATH.exists()


def test_valid_envelope_passes(schema: dict) -> None:
    jsonschema.validate(
        {
            "version": "1",
            "event_id": "e1",
            "run_id": "r1",
            "timestamp": "2026-06-13T10:00:00Z",
            "type": "task_started",
            "scope": {"task_id": "t1"},
        },
        schema,
    )


def test_missing_required_field_fails(schema: dict) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {"version": "1", "event_id": "e1", "type": "x", "scope": {}}, schema
        )  # missing run_id + timestamp


def test_unknown_envelope_version_fails(schema: dict) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "version": "99",
                "event_id": "e1",
                "run_id": "r1",
                "timestamp": "2026-06-13T10:00:00Z",
                "type": "task_started",
                "scope": {},
            },
            schema,
        )
