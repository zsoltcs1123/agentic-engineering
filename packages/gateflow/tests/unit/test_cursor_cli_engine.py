from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from gateflow.engines import CursorCLIEngine, EngineError, ExecutionEngine


def _ndjson(*events: dict) -> bytes:
    return "\n".join(json.dumps(e) for e in events).encode()


def _make_mock_process(
    *,
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int = 0,
) -> AsyncMock:
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.returncode = returncode
    return proc


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


@pytest.mark.unit
def test_conforms_to_execution_engine_protocol():
    assert isinstance(CursorCLIEngine(), ExecutionEngine)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_stream_json_output():
    stdout = _ndjson(ASSISTANT_EVENT, TOOL_STARTED_EVENT, TOOL_COMPLETED_EVENT, RESULT_EVENT)
    proc = _make_mock_process(stdout=stdout)

    with patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        engine = CursorCLIEngine()
        result = await engine.run(
            prompt="Do stuff",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert result.output == "Hello world"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["tool"] == "read"
    assert result.tool_calls[0]["args"] == {"path": "/tmp/foo.py"}
    assert result.tool_calls[0]["result"] == {"success": {"totalLines": 42}}
    assert result.duration_s == 3.5
    assert result.token_usage is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accumulates_multiple_assistant_chunks():
    events = [
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Part 1. "}]},
        },
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Part 2."}]},
        },
        RESULT_EVENT,
    ]
    proc = _make_mock_process(stdout=_ndjson(*events))

    with patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        result = await CursorCLIEngine().run(
            prompt="x",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert result.output == "Part 1. Part 2."


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_edits_adds_force_flag():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine().run(
            prompt="edit files",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="acceptEdits",
        )

    args = mock_exec.call_args.args
    assert "--force" in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readonly_adds_mode_ask():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine().run(
            prompt="read only",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="readonly",
        )

    args = mock_exec.call_args.args
    assert "--mode" in args
    mode_idx = args.index("--mode")
    assert args[mode_idx + 1] == "ask"
    assert "--force" not in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_mode_has_no_force_or_ask():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine().run(
            prompt="do things",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    args = mock_exec.call_args.args
    assert "--force" not in args
    assert "--mode" not in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_model_passed_to_cli():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine(model="gpt-5.2").run(
            prompt="hello",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    args = mock_exec.call_args.args
    assert "--model" in args
    model_idx = args.index("--model")
    assert args[model_idx + 1] == "gpt-5.2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_agent_path():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine(agent_path="/usr/local/bin/agent").run(
            prompt="hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert mock_exec.call_args.args[0] == "/usr/local/bin/agent"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nonzero_exit_code_raises_engine_error():
    proc = _make_mock_process(returncode=1, stderr=b"something went wrong")

    with (
        patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc),
        pytest.raises(EngineError, match="exited with code 1"),
    ):
        await CursorCLIEngine().run(
            prompt="fail",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nonzero_exit_includes_stderr_content():
    proc = _make_mock_process(returncode=2, stderr=b"auth token expired")

    with (
        patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc),
        pytest.raises(EngineError, match="auth token expired"),
    ):
        await CursorCLIEngine().run(
            prompt="fail",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_malformed_json_raises_engine_error():
    proc = _make_mock_process(stdout=b"not json at all\n")

    with (
        patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc),
        pytest.raises(EngineError, match="Malformed JSON"),
    ):
        await CursorCLIEngine().run(
            prompt="bad output",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_output_returns_empty_string():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch("gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        result = await CursorCLIEngine().run(
            prompt="nothing",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert result.output == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_working_directory_passed_as_cwd():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine().run(
            prompt="check",
            working_directory="/home/user/project",
            allowed_tools=[],
            permission_mode="default",
        )

    assert mock_exec.call_args.kwargs["cwd"] == "/home/user/project"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_not_found_raises_engine_error():
    with (
        patch(
            "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("No such file"),
        ),
        pytest.raises(EngineError, match="Cursor CLI not found"),
    ):
        await CursorCLIEngine(agent_path="/nonexistent/agent").run(
            prompt="hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompt_is_last_argument():
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "gateflow.engines.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLIEngine().run(
            prompt="my specific prompt",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert mock_exec.call_args.args[-1] == "my specific prompt"
