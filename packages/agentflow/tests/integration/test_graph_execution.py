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


def _make_initial_state(
    task: str = "implement the feature",
    workdir: str = "/tmp/project",
    max_review_cycles: int = 3,
) -> WorkflowState:
    return WorkflowState(
        task=task,
        workdir=workdir,
        review_passed=False,
        review_cycles=0,
        max_review_cycles=max_review_cycles,
        trace=[],
    )


def _make_mock_engine(side_effects: list[EngineResult]) -> CursorCLI:
    with patch("agentflow.engine.cursor_cli.shutil.which", return_value="agent"):
        engine = CursorCLI()
    engine.run = AsyncMock(side_effect=side_effects)
    return engine


async def _run_to_completion(graph, initial_state, config) -> dict:
    await graph.ainvoke(initial_state, config)
    for _ in range(20):
        state = await graph.aget_state(config)
        if not state.next:
            break
        await graph.ainvoke(None, config)
    return (await graph.aget_state(config)).values


@pytest.mark.integration
@pytest.mark.asyncio
async def test_happy_path_runs_all_four_steps(tmp_path: Path) -> None:
    engine = _make_mock_engine(
        [
            _make_engine_result("implemented changes"),
            _make_engine_result("LGTM, no issues found"),
            _make_engine_result("docs updated"),
            _make_engine_result("committed and pushed"),
        ]
    )
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(engine, checkpointer=checkpointer)
        values = await _run_to_completion(
            graph, _make_initial_state(), {"configurable": {"thread_id": "test-1"}}
        )

    assert len(values["trace"]) == 4
    assert [t.step for t in values["trace"]] == ["implement", "review", "document", "finalize"]
    assert values["review_passed"] is True
    assert values["review_cycles"] == 1

    await checkpointer.conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_loop_retries_then_passes(tmp_path: Path) -> None:
    engine = _make_mock_engine(
        [
            _make_engine_result("first attempt"),
            _make_engine_result("Found 2 bugs: missing null check, off-by-one error"),
            _make_engine_result("second attempt with fixes"),
            _make_engine_result("LGTM, all issues resolved"),
            _make_engine_result("docs updated"),
            _make_engine_result("committed"),
        ]
    )
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(engine, checkpointer=checkpointer)
        values = await _run_to_completion(
            graph, _make_initial_state(), {"configurable": {"thread_id": "test-2"}}
        )

    assert len(values["trace"]) == 6
    steps = [t.step for t in values["trace"]]
    assert steps == ["implement", "review", "implement", "review", "document", "finalize"]
    assert values["review_passed"] is True
    assert values["review_cycles"] == 2

    await checkpointer.conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_review_loop_exhausts_max_cycles(tmp_path: Path) -> None:
    engine = _make_mock_engine(
        [
            _make_engine_result("attempt 1"),
            _make_engine_result("bugs found"),
            _make_engine_result("attempt 2"),
            _make_engine_result("still bugs"),
            _make_engine_result("docs updated"),
            _make_engine_result("committed"),
        ]
    )
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(engine, checkpointer=checkpointer)
        values = await _run_to_completion(
            graph,
            _make_initial_state(max_review_cycles=2),
            {"configurable": {"thread_id": "test-3"}},
        )

    assert len(values["trace"]) == 6
    steps = [t.step for t in values["trace"]]
    assert steps == ["implement", "review", "implement", "review", "document", "finalize"]
    assert values["review_passed"] is False
    assert values["review_cycles"] == 2

    await checkpointer.conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prompts_contain_expected_context(tmp_path: Path) -> None:
    engine = _make_mock_engine(
        [
            _make_engine_result("implemented"),
            _make_engine_result("PASS"),
            _make_engine_result("documented"),
            _make_engine_result("finalized"),
        ]
    )
    checkpointer = await create_checkpointer(str(tmp_path / "test.db"))

    with (
        patch("agentflow.workflow.graph.print_engine_input"),
        patch("agentflow.workflow.graph.print_engine_output"),
    ):
        graph = build_graph(engine, checkpointer=checkpointer)
        await _run_to_completion(
            graph,
            _make_initial_state(task="add caching layer", workdir="/home/dev/myapp"),
            {"configurable": {"thread_id": "test-4"}},
        )

    calls = engine.run.call_args_list

    def _get_prompt(call) -> str:
        if call.args:
            return call.args[0]
        return call.kwargs["prompt"]

    assert "add caching layer" in _get_prompt(calls[0])
    assert "/home/dev/myapp" in _get_prompt(calls[1])
    assert "/home/dev/myapp" in _get_prompt(calls[2])
    assert "/home/dev/myapp" in _get_prompt(calls[3])

    await checkpointer.conn.close()
