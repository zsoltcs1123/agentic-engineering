import pytest
from pydantic import ValidationError

from gateflow import GateDecision, NodeOutput


@pytest.mark.unit
class TestNodeOutput:
    def test_rejects_confidence_above_one(self):
        with pytest.raises(ValidationError):
            NodeOutput(
                reasoning="r",
                assumptions=[],
                confidence=1.5,
                blind_spots=[],
                output="o",
            )

    def test_rejects_confidence_below_zero(self):
        with pytest.raises(ValidationError):
            NodeOutput(
                reasoning="r",
                assumptions=[],
                confidence=-0.1,
                blind_spots=[],
                output="o",
            )

    @pytest.mark.parametrize("value", [0.0, 0.75, 1.0])
    def test_accepts_valid_confidence(self, value):
        node = NodeOutput(
            reasoning="r",
            assumptions=["a"],
            confidence=value,
            blind_spots=["b"],
            output="o",
        )
        assert node.confidence == value


@pytest.mark.unit
class TestGateDecision:
    def test_rejects_invalid_verdict(self):
        with pytest.raises(ValidationError):
            GateDecision(
                verdict="MAYBE",  # pyright: ignore[reportArgumentType]
                reasoning="r",
                evidence=[],
                blind_spots=[],
            )

    def test_accepts_issues_verdict(self):
        decision = GateDecision(
            verdict="ISSUES",
            reasoning="found problems",
            evidence=["lint errors"],
            blind_spots=[],
            issues=["missing import"],
        )
        assert decision.verdict == "ISSUES"
        assert decision.issues == ["missing import"]

    def test_issues_defaults_to_empty_list(self):
        decision = GateDecision(
            verdict="PASS",
            reasoning="r",
            evidence=[],
            blind_spots=[],
        )
        assert decision.issues == []
