import pytest
from pymoldock_bench.runner import classify_outcome, EpisodeStatus

def test_needs_input_is_human_assist():
    assert classify_outcome("needs_input") == EpisodeStatus.HUMAN_ASSIST_REQUIRED

def test_active_outcome_rejected():
    with pytest.raises(ValueError): classify_outcome("in_progress")

