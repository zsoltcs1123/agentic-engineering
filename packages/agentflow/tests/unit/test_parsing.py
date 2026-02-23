from __future__ import annotations

import json

import pytest
from agentflow.engine.parsing import _try_parse_json, extract_tool_name, parse_events

ASSISTANT_EVENT = {
    "type": "assistant",
    "message": {"role": "assistant", "content": [{"type": "text", "text": "Hello world"}]},
}

TOOL_STARTED_EVENT = {
    "type": "tool_call",
    "subtype": "started",
    "tool_call": {
        "readToolCall": {
            "args": {"path": "/tmp/foo.py"},
        }
    },
}

TOOL_COMPLETED_EVENT = {
    "type": "tool_call",
    "subtype": "completed",
    "tool_call": {
        "readToolCall": {
            "args": {"path": "/tmp/foo.py"},
            "result": {"success": {"totalLines": 42}},
        }
    },
}

RESULT_EVENT = {
    "type": "result",
    "subtype": "success",
    "duration_ms": 3500,
}


def _to_lines(*events: dict) -> list[str]:
    return [json.dumps(e) for e in events]


@pytest.mark.unit
class TestExtractToolName:
    def test_returns_base_name_for_tool_call_key(self) -> None:
        assert extract_tool_name({"readToolCall": {}}) == "read"

    def test_returns_unknown_when_no_tool_call_key(self) -> None:
        assert extract_tool_name({"something": {}}) == "unknown"

    def test_returns_unknown_for_empty_dict(self) -> None:
        assert extract_tool_name({}) == "unknown"

    def test_handles_multi_word_tool_name(self) -> None:
        assert extract_tool_name({"listDirectoryToolCall": {}}) == "listDirectory"


@pytest.mark.unit
class TestParseEvents:
    def test_full_stream_produces_text_tools_and_duration(self) -> None:
        lines = _to_lines(ASSISTANT_EVENT, TOOL_STARTED_EVENT, TOOL_COMPLETED_EVENT, RESULT_EVENT)
        text, tool_calls, duration_s = parse_events(lines)

        assert text == "Hello world"
        assert len(tool_calls) == 1
        assert tool_calls[0].tool == "read"
        assert tool_calls[0].args == {"path": "/tmp/foo.py"}
        assert tool_calls[0].result == {"success": {"totalLines": 42}}
        assert duration_s == 3.5

    def test_multiple_assistant_chunks_accumulate(self) -> None:
        events = [
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Part 1. "}],
                },
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Part 2."}],
                },
            },
            RESULT_EVENT,
        ]
        text, _, _ = parse_events(_to_lines(*events))
        assert text == "Part 1. Part 2."

    def test_tool_call_lifecycle_tracks_started_and_completed(self) -> None:
        lines = _to_lines(TOOL_STARTED_EVENT, TOOL_COMPLETED_EVENT)
        _, tool_calls, _ = parse_events(lines)

        assert len(tool_calls) == 1
        assert tool_calls[0].result == {"success": {"totalLines": 42}}

    def test_tool_call_without_completed_has_empty_result(self) -> None:
        lines = _to_lines(TOOL_STARTED_EVENT)
        _, tool_calls, _ = parse_events(lines)

        assert len(tool_calls) == 1
        assert tool_calls[0].result == {}

    def test_duration_extracted_from_result_event(self) -> None:
        lines = _to_lines(RESULT_EVENT)
        _, _, duration_s = parse_events(lines)
        assert duration_s == 3.5

    def test_empty_lines_skipped(self) -> None:
        lines = ["", "  ", json.dumps(RESULT_EVENT), ""]
        _, _, duration_s = parse_events(lines)
        assert duration_s == 3.5

    def test_invalid_json_skipped(self) -> None:
        lines = ["not json", json.dumps(RESULT_EVENT)]
        _, _, duration_s = parse_events(lines)
        assert duration_s == 3.5

    def test_empty_input_returns_defaults(self) -> None:
        text, tool_calls, duration_s = parse_events([])
        assert text == ""
        assert tool_calls == []
        assert duration_s == 0.0


@pytest.mark.unit
class TestTryParseJson:
    def test_valid_json_parsed(self) -> None:
        assert _try_parse_json('{"key": "value"}') == {"key": "value"}

    def test_invalid_json_returns_none(self) -> None:
        assert _try_parse_json("not json") is None

    def test_empty_string_returns_none(self) -> None:
        assert _try_parse_json("") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert _try_parse_json("   ") is None
