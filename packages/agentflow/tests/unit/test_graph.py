from __future__ import annotations

from unittest.mock import patch

import pytest
from agentflow.engine import CursorCLI, EngineResult
from agentflow.engine.types import ToolCallEntry
from agentflow.workflow.graph import _make_trace_entry, build_graph


@pytest.fixture()
def engine() -> CursorCLI:
    with patch("agentflow.engine.cursor_cli.shutil.which", return_value="agent"):
        return CursorCLI()


@pytest.mark.unit
class TestMakeTraceEntry:
    def test_maps_engine_result_fields(self) -> None:
        result = EngineResult(
            output="plan output",
            tool_calls=[ToolCallEntry(tool="read"), ToolCallEntry(tool="write")],
            duration_s=4.2,
        )
        entry = _make_trace_entry("plan", "Create a plan for X", result)

        assert entry.step == "plan"
        assert entry.prompt_len == len("Create a plan for X")
        assert entry.output == "plan output"
        assert entry.duration_s == 4.2
        assert entry.tool_call_count == 2

    def test_zero_tool_calls(self) -> None:
        result = EngineResult(output="done", tool_calls=[], duration_s=1.0)
        entry = _make_trace_entry("review", "Review changes", result)
        assert entry.tool_call_count == 0


@pytest.mark.unit
class TestBuildGraph:
    def test_graph_contains_expected_nodes(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        node_names = set(graph.get_graph().nodes.keys())
        assert {"plan", "implement", "review"} <= node_names

    def test_edges_form_linear_pipeline(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        edges = {(e.source, e.target) for e in graph.get_graph().edges}
        assert ("__start__", "plan") in edges
        assert ("plan", "implement") in edges
        assert ("implement", "review") in edges
        assert ("review", "__end__") in edges
