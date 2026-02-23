from __future__ import annotations

import pytest
from agentflow.workflow.display import _truncate


@pytest.mark.unit
class TestTruncate:
    def test_short_text_returned_unchanged(self) -> None:
        assert _truncate("hello", limit=100) == "hello"

    def test_text_at_exact_limit_returned_unchanged(self) -> None:
        text = "a" * 50
        assert _truncate(text, limit=50) == text

    def test_text_over_limit_truncated_with_char_count(self) -> None:
        text = "a" * 200
        result = _truncate(text, limit=100)
        assert result.startswith("a" * 100)
        assert "200 chars total" in result

    def test_uses_default_limit(self) -> None:
        short = "x" * 1999
        assert _truncate(short) == short

        long = "x" * 2001
        assert "2001 chars total" in _truncate(long)
