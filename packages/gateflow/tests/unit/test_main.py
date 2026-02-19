import pytest

from gateflow.main import main


@pytest.mark.unit
def test_main_function_exists() -> None:
    assert callable(main)


@pytest.mark.unit
def test_main_function_runs(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    captured = capsys.readouterr()
    assert "gateflow" in captured.out
