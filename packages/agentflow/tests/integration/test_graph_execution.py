from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from agentflow.engine import CursorCLI, EngineResult
from agentflow.workflow.checkpointer import create_checkpointer
from agentflow.workflow.graph import build_graph
from agentflow.workflow.state import WorkflowState


def _make_engine_result(output: str) -> EngineResult:
    return EngineResult(output=output, tool_calls=[], duration_s=1.0)


@pytest.fixture()
def mock_engine() -> CursorCLI:
    with patch("agentflow.engine.cursor_cli.shutil.which", return_value="agent"):
        engine = CursorCLI()
    engine.run = AsyncMock(
        side_effect=[
            _make_engine_result("Step 1: do X\nStep 2: do Y"),
            _make_engine_result("implemented changes"),
            _make_engine_result("LGTM, all good"),
        ]
    )
    return engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graph_runs_all_steps_and_accumulates_trace(
    tmp_path: Path, mock_engine: CursorCLI
) -> None:
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(mock_engine, checkpointer=checkpointer)

        initial_state = WorkflowState(
            task="fix the bug",
            workdir="/tmp/project",
            plan="",
            review="",
            trace=[],
        )
        config = {"configurable": {"thread_id": "test-1"}}

        await graph.ainvoke(initial_state, config)
        state = await graph.aget_state(config)

        if state.next:
            await graph.ainvoke(None, config)
            state = await graph.aget_state(config)

        if state.next:
            await graph.ainvoke(None, config)
            state = await graph.aget_state(config)

        if state.next:
            await graph.ainvoke(None, config)
            state = await graph.aget_state(config)

    values = state.values
    assert values["plan"] == "Step 1: do X\nStep 2: do Y"
    assert values["review"] == "LGTM, all good"
    assert len(values["trace"]) == 3
    assert [t.step for t in values["trace"]] == ["plan", "implement", "review"]

    await checkpointer.conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graph_passes_correct_prompts_to_engine(
    tmp_path: Path, mock_engine: CursorCLI
) -> None:
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(mock_engine, checkpointer=checkpointer)

        initial_state = WorkflowState(
            task="add tests",
            workdir="/tmp/project",
            plan="",
            review="",
            trace=[],
        )
        config = {"configurable": {"thread_id": "test-2"}}

        await graph.ainvoke(initial_state, config)
        for _ in range(3):
            state = await graph.aget_state(config)
            if not state.next:
                break
            await graph.ainvoke(None, config)

    calls = mock_engine.run.call_args_list
    assert "add tests" in calls[0].kwargs.get("prompt", calls[0].args[0] if calls[0].args else "")

    plan_prompt = calls[1].kwargs.get("prompt", calls[1].args[0] if calls[1].args else "")
    assert "Step 1: do X" in plan_prompt

    review_prompt = calls[2].kwargs.get("prompt", calls[2].args[0] if calls[2].args else "")
    assert "/tmp/project" in review_prompt

    await checkpointer.conn.close()
