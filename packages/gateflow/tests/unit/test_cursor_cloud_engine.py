from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from gateflow.engines import EngineError, ExecutionEngine
from gateflow.engines.cursor_cloud import CursorCloudEngine

_DUMMY_REQUEST = httpx.Request("GET", "https://api.cursor.com/v0/agents")


def _json_response(data: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=data, request=_DUMMY_REQUEST)


def _text_response(text: str, status_code: int) -> httpx.Response:
    return httpx.Response(status_code=status_code, text=text, request=_DUMMY_REQUEST)


AGENT_ID = "bc_test123"
REPO = "https://github.com/test-org/test-repo"

STATUS_CREATING = {"id": AGENT_ID, "status": "CREATING"}
STATUS_RUNNING = {"id": AGENT_ID, "status": "RUNNING"}
STATUS_FINISHED = {
    "id": AGENT_ID,
    "status": "FINISHED",
    "summary": "Implemented the feature",
}
STATUS_FAILED = {
    "id": AGENT_ID,
    "status": "FAILED",
    "summary": "Compilation error in main.py",
}
STATUS_STOPPED = {"id": AGENT_ID, "status": "STOPPED"}

CONVERSATION = {
    "id": AGENT_ID,
    "messages": [
        {"id": "msg_001", "type": "user_message", "text": "Do the thing"},
        {"id": "msg_002", "type": "assistant_message", "text": "I'll help with that."},
        {"id": "msg_003", "type": "assistant_message", "text": "Done. Here are the changes."},
    ],
}

CREATE_RESPONSE = {"id": AGENT_ID, "status": "CREATING"}


def _make_engine(
    client: httpx.AsyncClient | None = None,
    **kwargs: object,
) -> CursorCloudEngine:
    defaults: dict = {
        "repository": REPO,
        "api_key": "key_test",
        "poll_interval_s": 0.0,
        "poll_timeout_s": 5.0,
    }
    defaults.update(kwargs)
    return CursorCloudEngine(client=client, **defaults)


def _mock_client(*responses: httpx.Response) -> AsyncMock:
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request = AsyncMock(side_effect=list(responses))
    return client


@pytest.mark.unit
def test_conforms_to_execution_engine_protocol():
    engine = _make_engine()
    assert isinstance(engine, ExecutionEngine)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_happy_path_returns_conversation_output():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    result = await engine.run(
        prompt="Implement feature X",
        working_directory="/home/user/my-project",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == "I'll help with that.\n\nDone. Here are the changes."
    assert result.duration_s > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_polls_through_non_terminal_statuses():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_CREATING),
        _json_response(STATUS_RUNNING),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    result = await engine.run(
        prompt="Do work",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == "I'll help with that.\n\nDone. Here are the changes."
    assert client.request.call_count == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_timeout_raises_engine_error():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_RUNNING),
        _json_response(STATUS_RUNNING),
        _json_response(STATUS_RUNNING),
    )
    engine = _make_engine(client=client, poll_timeout_s=0.0)

    with pytest.raises(EngineError, match="did not complete"):
        await engine.run(
            prompt="Slow task",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_error_raises_engine_error():
    client = _mock_client(
        _text_response("Unauthorized", 401),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="authentication failed"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_forbidden_error_includes_repository():
    client = _mock_client(
        _text_response("Forbidden", 403),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="access denied.*test-repo"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_raises_engine_error():
    client = _mock_client(
        _text_response("Too Many Requests", 429),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="rate limit"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_server_error_includes_status_and_body():
    client = _mock_client(
        _text_response("Bad Gateway", 502),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="status 502.*Bad Gateway"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failed_agent_raises_engine_error_with_summary():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FAILED),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="failed.*Compilation error"):
        await engine.run(
            prompt="Build",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stopped_agent_raises_engine_error():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_STOPPED),
    )
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="was stopped"):
        await engine.run(
            prompt="Do stuff",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_branch_derived_from_working_directory():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    await engine.run(
        prompt="Hi",
        working_directory="/home/user/worktrees/task-042",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["target"]["branchName"] == "gateflow/task-042"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_custom_model_sent_to_api():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client, model="claude-4-sonnet")

    await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["model"] == "claude-4-sonnet"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_model_omits_field_from_request():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert "model" not in body


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auto_create_pr_forwarded():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client, auto_create_pr=True)

    await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["target"]["autoCreatePr"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ref_sent_in_source():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client, ref="develop")

    await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["source"]["ref"] == "develop"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_conversation_fallback_to_summary():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _text_response("Not Found", 404),
    )
    engine = _make_engine(client=client)

    result = await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == "Implemented the feature"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connection_error_raises_engine_error():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="Failed to connect"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_timeout_raises_engine_error():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request = AsyncMock(side_effect=httpx.ReadTimeout("Read timed out"))
    engine = _make_engine(client=client)

    with pytest.raises(EngineError, match="timed out"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp/proj",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
def test_missing_api_key_raises_engine_error():
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(EngineError, match="API key not provided"),
    ):
        CursorCloudEngine(repository=REPO)


@pytest.mark.unit
def test_api_key_from_env_var():
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_from_env"}):
        engine = CursorCloudEngine(repository=REPO)
        assert engine._api_key == "key_from_env"


@pytest.mark.unit
def test_explicit_api_key_takes_precedence():
    with patch.dict("os.environ", {"CURSOR_API_KEY": "key_from_env"}):
        engine = CursorCloudEngine(repository=REPO, api_key="key_explicit")
        assert engine._api_key == "key_explicit"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prompt_sent_in_create_body():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    await engine.run(
        prompt="Implement the login feature",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["prompt"]["text"] == "Implement the login feature"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_repository_sent_in_create_body():
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(CONVERSATION),
    )
    engine = _make_engine(client=client)

    await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    create_call = client.request.call_args_list[0]
    body = create_call.kwargs.get("json") or create_call[1].get("json")
    assert body["source"]["repository"] == REPO


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_conversation_falls_back_to_summary():
    empty_conversation = {"id": AGENT_ID, "messages": []}
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(empty_conversation),
    )
    engine = _make_engine(client=client)

    result = await engine.run(
        prompt="Hi",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_filters_only_assistant_messages():
    conversation = {
        "id": AGENT_ID,
        "messages": [
            {"id": "m1", "type": "user_message", "text": "Do X"},
            {"id": "m2", "type": "assistant_message", "text": "Done."},
            {"id": "m3", "type": "user_message", "text": "Also Y"},
            {"id": "m4", "type": "assistant_message", "text": "Y is done too."},
        ],
    }
    client = _mock_client(
        _json_response(CREATE_RESPONSE),
        _json_response(STATUS_FINISHED),
        _json_response(conversation),
    )
    engine = _make_engine(client=client)

    result = await engine.run(
        prompt="Do X",
        working_directory="/tmp/proj",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == "Done.\n\nY is done too."
