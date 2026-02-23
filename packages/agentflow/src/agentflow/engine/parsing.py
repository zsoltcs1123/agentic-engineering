from __future__ import annotations

import json
from typing import Any

from agentflow.engine.types import ToolCallEntry


def extract_tool_name(tool_call_data: dict[str, Any]) -> str:
    for key in tool_call_data:
        if key.endswith("ToolCall"):
            return key.removesuffix("ToolCall")
    return "unknown"


def parse_events(raw_lines: list[str]) -> tuple[str, list[ToolCallEntry], float]:
    text_parts: list[str] = []
    tool_calls: list[ToolCallEntry] = []
    duration_s: float = 0.0
    pending_tools: dict[str, ToolCallEntry] = {}

    for raw in raw_lines:
        event = _try_parse_json(raw)
        if event is None:
            continue

        event_type = event.get("type")
        if event_type == "assistant":
            _collect_text(event, text_parts)
        elif event_type == "tool_call":
            _collect_tool_call(event, tool_calls, pending_tools)
        elif event_type == "result":
            duration_s = event.get("duration_ms", 0) / 1000.0

    return "".join(text_parts), tool_calls, duration_s


def _try_parse_json(raw: str) -> dict[str, Any] | None:
    line = raw.strip()
    if not line:
        return None
    try:
        parsed: dict[str, Any] = json.loads(line)
    except json.JSONDecodeError:
        return None
    return parsed


def _collect_text(event: dict[str, Any], text_parts: list[str]) -> None:
    content = event.get("message", {}).get("content", [])
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))


def _collect_tool_call(
    event: dict[str, Any],
    tool_calls: list[ToolCallEntry],
    pending_tools: dict[str, ToolCallEntry],
) -> None:
    subtype = event.get("subtype")
    call_data = event.get("tool_call", {})
    tool_name = extract_tool_name(call_data)
    tool_payload = call_data.get(f"{tool_name}ToolCall", {})

    if subtype == "started":
        entry = ToolCallEntry(
            tool=tool_name,
            args=tool_payload.get("args", {}),
        )
        pending_tools[tool_name] = entry
        tool_calls.append(entry)
    elif subtype == "completed" and tool_name in pending_tools:
        pending_tools[tool_name].result = tool_payload.get("result", {})
        del pending_tools[tool_name]
