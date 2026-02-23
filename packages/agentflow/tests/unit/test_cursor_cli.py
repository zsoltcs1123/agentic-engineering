from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from agentflow.engine import CursorCLI, EngineError


@pytest.fixture(autouse=True)
def _fake_which(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agentflow.engine.cursor_cli.shutil.which",
        lambda p: p,
    )


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

RESULT_EVENT = {
    "type": "result",
    "subtype": "success",
    "duration_ms": 3500,
}

TOOL_STARTED_EVENT = {
    "type": "tool_call",
    "subtype": "started",
    "tool_call": {"readToolCall": {"args": {"path": "/tmp/foo.py"}}},
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


@pytest.mark.unit
def test_which_returns_none_raises_engine_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agentflow.engine.cursor_cli.shutil.which",
        lambda _p: None,
    )
    with pytest.raises(EngineError, match="not found on PATH"):
        CursorCLI(agent_path="nonexistent-binary")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_stream_json_output() -> None:
    stdout = _ndjson(ASSISTANT_EVENT, TOOL_STARTED_EVENT, TOOL_COMPLETED_EVENT, RESULT_EVENT)
    proc = _make_mock_process(stdout=stdout)

    with patch("agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        result = await CursorCLI().run(
            prompt="Do stuff",
            working_directory="/tmp",
        )

    assert result.output == "Hello world"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool == "read"
    assert result.duration_s == 3.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accept_edits_adds_force_flag() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLI().run(
            prompt="edit files",
            working_directory="/tmp",
            mode="acceptEdits",
        )

    args = mock_exec.call_args.args
    assert "--force" in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readonly_adds_mode_ask() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLI().run(
            prompt="read only",
            working_directory="/tmp",
            mode="readonly",
        )

    args = mock_exec.call_args.args
    assert "--mode" in args
    mode_idx = args.index("--mode")
    assert args[mode_idx + 1] == "ask"
    assert "--force" not in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_mode_has_no_force_or_ask() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLI().run(
            prompt="do things",
            working_directory="/tmp",
            mode="default",
        )

    args = mock_exec.call_args.args
    assert "--force" not in args
    assert "--mode" not in args


@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_model_passed_to_cli() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLI(model="gpt-5.2").run(
            prompt="hello",
            working_directory="/tmp",
        )

    args = mock_exec.call_args.args
    assert "--model" in args
    model_idx = args.index("--model")
    assert args[model_idx + 1] == "gpt-5.2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nonzero_exit_code_raises_engine_error() -> None:
    proc = _make_mock_process(returncode=1, stderr=b"something went wrong")

    with (
        patch("agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc),
        pytest.raises(EngineError, match="exited with code 1"),
    ):
        await CursorCLI().run(prompt="fail", working_directory="/tmp")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nonzero_exit_includes_stderr_content() -> None:
    proc = _make_mock_process(returncode=2, stderr=b"auth token expired")

    with (
        patch("agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc),
        pytest.raises(EngineError, match="auth token expired"),
    ):
        await CursorCLI().run(prompt="fail", working_directory="/tmp")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_not_found_raises_engine_error() -> None:
    with (
        patch(
            "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("No such file"),
        ),
        pytest.raises(EngineError, match="Cursor CLI not found"),
    ):
        await CursorCLI(agent_path="/nonexistent/agent").run(
            prompt="hi",
            working_directory="/tmp",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_os_error_raises_engine_error() -> None:
    with (
        patch(
            "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec",
            side_effect=OSError("Permission denied"),
        ),
        pytest.raises(EngineError, match="Failed to start Cursor CLI"),
    ):
        await CursorCLI().run(prompt="hi", working_directory="/tmp")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_working_directory_passed_as_cwd() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch(
        "agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc
    ) as mock_exec:
        await CursorCLI().run(
            prompt="check",
            working_directory="/home/user/project",
        )

    assert mock_exec.call_args.kwargs["cwd"] == "/home/user/project"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompt_sent_to_stdin() -> None:
    proc = _make_mock_process(stdout=_ndjson(RESULT_EVENT))

    with patch("agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        await CursorCLI().run(prompt="my specific prompt", working_directory="/tmp")

    proc.communicate.assert_awaited_once()
    assert proc.communicate.call_args.kwargs["input"] == b"my specific prompt"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_output_falls_back_to_elapsed_when_duration_zero() -> None:
    result_no_duration = {"type": "result", "subtype": "success", "duration_ms": 0}
    proc = _make_mock_process(stdout=_ndjson(result_no_duration))

    with patch("agentflow.engine.cursor_cli.asyncio.create_subprocess_exec", return_value=proc):
        result = await CursorCLI().run(prompt="x", working_directory="/tmp")

    assert result.duration_s > 0
