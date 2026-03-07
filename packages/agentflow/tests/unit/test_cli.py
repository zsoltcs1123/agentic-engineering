from __future__ import annotations

import pytest
from agentflow.cli import _parse_args


@pytest.mark.unit
class TestParseArgs:
    def test_run_with_task(self) -> None:
        args = _parse_args(["run", "fix the bug"])
        assert args.command == "run"
        assert args.task == "fix the bug"

    def test_defaults_for_workdir_and_model(self) -> None:
        args = _parse_args(["run", "do something"])
        assert args.workdir == "."
        assert args.model is None

    def test_explicit_workdir_and_model(self) -> None:
        args = _parse_args(["run", "task", "--workdir", "/tmp/proj", "--model", "gpt-5"])
        assert args.workdir == "/tmp/proj"
        assert args.model == "gpt-5"

    def test_default_max_review_cycles(self) -> None:
        args = _parse_args(["run", "some task"])
        assert args.max_review_cycles == 3

    def test_explicit_max_review_cycles(self) -> None:
        args = _parse_args(["run", "some task", "--max-review-cycles", "5"])
        assert args.max_review_cycles == 5

    def test_missing_subcommand_yields_none(self) -> None:
        args = _parse_args([])
        assert args.command is None
