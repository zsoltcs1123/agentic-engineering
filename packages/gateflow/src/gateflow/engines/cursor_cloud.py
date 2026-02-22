from __future__ import annotations

import asyncio
import os
import time
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

import httpx

from gateflow.models import EngineError, EngineResult

if TYPE_CHECKING:
    from gateflow.engines import PermissionMode

_TERMINAL_STATUSES = frozenset({"FINISHED", "STOPPED", "FAILED"})


class CursorCloudEngine:
    def __init__(
        self,
        *,
        repository: str,
        api_key: str | None = None,
        base_url: str = "https://api.cursor.com",
        model: str | None = None,
        ref: str = "main",
        auto_create_pr: bool = False,
        poll_interval_s: float = 10.0,
        poll_timeout_s: float = 1800.0,
        poll_backoff_factor: float = 1.5,
        poll_max_interval_s: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("CURSOR_API_KEY")
        if not resolved_key:
            raise EngineError(
                "Cursor Cloud API key not provided. "
                "Pass api_key or set the CURSOR_API_KEY environment variable."
            )
        self._repository = repository
        self._api_key = resolved_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._ref = ref
        self._auto_create_pr = auto_create_pr
        self._poll_interval_s = poll_interval_s
        self._poll_timeout_s = poll_timeout_s
        self._poll_backoff_factor = poll_backoff_factor
        self._poll_max_interval_s = poll_max_interval_s
        self._client = client

    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(username=self._api_key, password="")

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    @staticmethod
    def _branch_from_workdir(working_directory: str) -> str:
        return f"gateflow/{PurePosixPath(working_directory).name}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        client = self._client or httpx.AsyncClient()
        owns_client = self._client is None
        try:
            response = await client.request(
                method,
                self._url(path),
                json=json_body,
                auth=self._auth(),
                timeout=30.0,
            )
        except httpx.ConnectError as exc:
            raise EngineError(f"Failed to connect to Cursor Cloud API: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise EngineError(f"Cursor Cloud API request timed out: {exc}") from exc
        finally:
            if owns_client:
                await client.aclose()

        if response.status_code == 401:
            raise EngineError("Cursor Cloud API authentication failed. Check CURSOR_API_KEY.")
        if response.status_code == 403:
            raise EngineError(f"Cursor Cloud API access denied for repository: {self._repository}")
        if response.status_code == 429:
            raise EngineError("Cursor Cloud API rate limit exceeded. Retry after backoff.")
        if response.status_code >= 500:
            raise EngineError(
                f"Cursor Cloud API error (status {response.status_code}): {response.text}"
            )
        if response.status_code == 404:
            raise EngineError(f"Cursor Cloud API resource not found: {path}")
        response.raise_for_status()
        return response

    async def _create_agent(self, prompt: str, branch: str) -> str:
        body: dict[str, Any] = {
            "prompt": {"text": prompt},
            "source": {
                "repository": self._repository,
                "ref": self._ref,
            },
            "target": {
                "branchName": branch,
                "autoCreatePr": self._auto_create_pr,
            },
        }
        if self._model:
            body["model"] = self._model

        response = await self._request("POST", "/v0/agents", json_body=body)
        data = response.json()
        agent_id: str = data["id"]
        return agent_id

    async def _get_status(self, agent_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/v0/agents/{agent_id}")
        return response.json()  # type: ignore[no-any-return]

    async def _get_conversation(self, agent_id: str) -> str:
        response = await self._request("GET", f"/v0/agents/{agent_id}/conversation")
        data = response.json()
        messages = data.get("messages", [])
        parts = [
            msg["text"]
            for msg in messages
            if msg.get("type") == "assistant_message" and msg.get("text")
        ]
        return "\n\n".join(parts)

    async def _poll_until_terminal(self, agent_id: str) -> dict[str, Any]:
        start = time.monotonic()
        interval = self._poll_interval_s

        while True:
            elapsed = time.monotonic() - start
            if elapsed >= self._poll_timeout_s:
                raise EngineError(
                    f"Cursor Cloud agent {agent_id} did not complete within {self._poll_timeout_s}s"
                )

            await asyncio.sleep(interval)
            status_data = await self._get_status(agent_id)

            if status_data.get("status") in _TERMINAL_STATUSES:
                return status_data

            interval = min(interval * self._poll_backoff_factor, self._poll_max_interval_s)

    async def run(
        self,
        prompt: str,
        working_directory: str,
        allowed_tools: list[str],
        permission_mode: PermissionMode,
    ) -> EngineResult:
        branch = self._branch_from_workdir(working_directory)
        start = time.monotonic()

        agent_id = await self._create_agent(prompt, branch)
        status_data = await self._poll_until_terminal(agent_id)

        duration = time.monotonic() - start
        status = status_data.get("status")

        if status == "FAILED":
            summary = status_data.get("summary", "unknown error")
            raise EngineError(f"Cursor Cloud agent {agent_id} failed: {summary}")

        if status == "STOPPED":
            raise EngineError(f"Cursor Cloud agent {agent_id} was stopped")

        try:
            output = await self._get_conversation(agent_id)
        except EngineError:
            output = status_data.get("summary", "")

        return EngineResult(output=output, duration_s=duration)
