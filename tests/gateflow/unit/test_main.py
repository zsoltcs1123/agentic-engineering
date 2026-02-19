"""Unit tests for main module."""

import pytest

from gateflow.main import main


@pytest.mark.unit
def test_main_function_exists() -> None:
    """Test that main function exists and is callable."""
    assert callable(main)


@pytest.mark.unit
def test_main_function_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that main function prints expected output."""
    main()
    captured = capsys.readouterr()
    assert "gateflow" in captured.out
