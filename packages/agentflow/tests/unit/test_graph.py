from __future__ import annotations

from unittest.mock import patch

import pytest
from agentflow.engine import CursorCLI, EngineResult
from agentflow.engine.types import ToolCallEntry
from agentflow.workflow.graph import _make_trace_entry, _review_passed, build_graph


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
class TestReviewPassed:
    @pytest.mark.parametrize(
        "text",
        [
            "LGTM, all good",
            "No issues found in this review.",
            "PASS",
            "Code looks good to me",
            "Changes approved, ready to merge",
            "I see no problems with this implementation",
        ],
    )
    def test_returns_true_for_pass_signals(self, text: str) -> None:
        assert _review_passed(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "Found 3 critical bugs that need fixing",
            "The error handling is insufficient",
            "Please refactor the database layer",
            "",
        ],
    )
    def test_returns_false_for_issues_or_ambiguous(self, text: str) -> None:
        assert _review_passed(text) is False


@pytest.mark.unit
class TestBuildGraph:
    def test_graph_contains_expected_nodes(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        node_names = set(graph.get_graph().nodes.keys())
        assert {"implement", "review", "document", "finalize"} <= node_names

    def test_graph_has_no_plan_node(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        node_names = set(graph.get_graph().nodes.keys())
        assert "plan" not in node_names

    def test_graph_edges_start_at_implement(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        edges = {(e.source, e.target) for e in graph.get_graph().edges}
        assert ("__start__", "implement") in edges

    def test_graph_edges_implement_to_review(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        edges = {(e.source, e.target) for e in graph.get_graph().edges}
        assert ("implement", "review") in edges

    def test_graph_edges_review_has_conditional_targets(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        edges = {(e.source, e.target) for e in graph.get_graph().edges}
        assert ("review", "implement") in edges
        assert ("review", "document") in edges

    def test_graph_edges_document_to_finalize_to_end(self, engine: CursorCLI) -> None:
        graph = build_graph(engine)
        edges = {(e.source, e.target) for e in graph.get_graph().edges}
        assert ("document", "finalize") in edges
        assert ("finalize", "__end__") in edges
