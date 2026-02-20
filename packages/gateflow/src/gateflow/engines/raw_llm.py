from __future__ import annotations

import time
from typing import TYPE_CHECKING

import anthropic
from anthropic.types import TextBlock

from gateflow.models import EngineError, EngineResult

if TYPE_CHECKING:
    from gateflow.engines import PermissionMode


class RawLLMEngine:
    def __init__(
        self,
        *,
        model: str = "claude-haiku-4-5-20251001",
        max_tokens: int = 4096,
        api_key: str | None = None,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)

    async def run(
        self,
        prompt: str,
        working_directory: str,
        allowed_tools: list[str],
        permission_mode: PermissionMode,
    ) -> EngineResult:
        messages: list[anthropic.types.MessageParam] = [{"role": "user", "content": prompt}]
        start = time.monotonic()
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=messages,
            )
        except anthropic.APIConnectionError as exc:
            raise EngineError(f"Failed to connect to Anthropic API: {exc}") from exc
        except anthropic.RateLimitError as exc:
            raise EngineError(f"Anthropic API rate limit exceeded: {exc.message}") from exc
        except anthropic.AuthenticationError as exc:
            raise EngineError(f"Anthropic API authentication failed: {exc.message}") from exc
        except anthropic.APIStatusError as exc:
            raise EngineError(
                f"Anthropic API error (status {exc.status_code}): {exc.message}"
            ) from exc
        duration = time.monotonic() - start

        text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                text = block.text
                break
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return EngineResult(output=text, token_usage=usage, duration_s=duration)
