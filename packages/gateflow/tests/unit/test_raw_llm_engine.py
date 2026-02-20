from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import anthropic
import pytest
from anthropic.types import TextBlock

from gateflow.engines import EngineError, ExecutionEngine, RawLLMEngine


def _make_mock_client(
    *,
    text: str = "Hello!",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> AsyncMock:
    usage = Mock(input_tokens=input_tokens, output_tokens=output_tokens)
    text_block = TextBlock(type="text", text=text)
    response = Mock(content=[text_block], usage=usage)
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    client.messages.create = AsyncMock(return_value=response)
    return client


@pytest.mark.unit
def test_conforms_to_execution_engine_protocol():
    engine = RawLLMEngine(client=AsyncMock(spec=anthropic.AsyncAnthropic))
    assert isinstance(engine, ExecutionEngine)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_response_text_in_output():
    client = _make_mock_client(text="Plan: do the thing")
    engine = RawLLMEngine(client=client)

    result = await engine.run(
        prompt="Create a plan",
        working_directory="/tmp",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.output == "Plan: do the thing"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_captures_token_usage():
    client = _make_mock_client(input_tokens=25, output_tokens=42)
    engine = RawLLMEngine(client=client)

    result = await engine.run(
        prompt="Hello",
        working_directory="/tmp",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.token_usage == {"input_tokens": 25, "output_tokens": 42}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_measures_positive_duration():
    client = _make_mock_client()
    engine = RawLLMEngine(client=client)

    result = await engine.run(
        prompt="Hello",
        working_directory="/tmp",
        allowed_tools=[],
        permission_mode="default",
    )

    assert result.duration_s > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_passes_custom_model_and_max_tokens():
    client = _make_mock_client()
    engine = RawLLMEngine(client=client, model="claude-haiku-3", max_tokens=512)

    await engine.run(
        prompt="Hi",
        working_directory="/tmp",
        allowed_tools=[],
        permission_mode="default",
    )

    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-3"
    assert call_kwargs["max_tokens"] == 512


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sends_prompt_as_user_message():
    client = _make_mock_client()
    engine = RawLLMEngine(client=client)

    await engine.run(
        prompt="Review the code",
        working_directory="/tmp",
        allowed_tools=[],
        permission_mode="default",
    )

    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": "Review the code"}]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wraps_rate_limit_error():
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_response = Mock(status_code=429, headers={})
    client.messages.create = AsyncMock(
        side_effect=anthropic.RateLimitError(
            message="rate limited",
            response=mock_response,
            body=None,
        )
    )
    engine = RawLLMEngine(client=client)

    with pytest.raises(EngineError, match="rate limit"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wraps_authentication_error():
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_response = Mock(status_code=401, headers={})
    client.messages.create = AsyncMock(
        side_effect=anthropic.AuthenticationError(
            message="invalid api key",
            response=mock_response,
            body=None,
        )
    )
    engine = RawLLMEngine(client=client)

    with pytest.raises(EngineError, match="authentication failed"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wraps_connection_error():
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    client.messages.create = AsyncMock(side_effect=anthropic.APIConnectionError(request=Mock()))
    engine = RawLLMEngine(client=client)

    with pytest.raises(EngineError, match="Failed to connect"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wraps_generic_api_status_error():
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_response = Mock(status_code=500, headers={})
    client.messages.create = AsyncMock(
        side_effect=anthropic.APIStatusError(
            message="internal server error",
            response=mock_response,
            body=None,
        )
    )
    engine = RawLLMEngine(client=client)

    with pytest.raises(EngineError, match="status 500"):
        await engine.run(
            prompt="Hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_engine_error_chains_original_exception():
    client = AsyncMock(spec=anthropic.AsyncAnthropic)
    original = anthropic.APIConnectionError(request=Mock())
    client.messages.create = AsyncMock(side_effect=original)
    engine = RawLLMEngine(client=client)

    with pytest.raises(EngineError) as exc_info:
        await engine.run(
            prompt="Hi",
            working_directory="/tmp",
            allowed_tools=[],
            permission_mode="default",
        )

    assert exc_info.value.__cause__ is original
