"""
tests/test_risk.py - Unit tests for deterministic risk rule truth table.
"""

import pytest
from alerts import compute_risk

def test_risk_non_elephant():
    """Non-elephant detections should always return risk NONE."""
    res_other = compute_risk('other_animal', 0.95, is_night=False, repeat_sighting=False)
    assert res_other['risk'] == 'NONE'
    assert not res_other['review_needed']

    res_none = compute_risk('no_animal', 0.99, is_night=True, repeat_sighting=True)
    assert res_none['risk'] == 'NONE'
    assert not res_none['review_needed']

def test_risk_elephant_daytime():
    """Elephant detection during day without repeat sighting."""
    # Confidence >= 0.85 -> Base MEDIUM
    res_med = compute_risk('elephant', 0.88, is_night=False, repeat_sighting=False)
    assert res_med['risk'] == 'MEDIUM'
    assert not res_med['review_needed']

    # Confidence < 0.85 -> Base LOW
    res_low = compute_risk('elephant', 0.70, is_night=False, repeat_sighting=False)
    assert res_low['risk'] == 'LOW'
    assert not res_low['review_needed']

def test_risk_elephant_night_elevation():
    """Night time elevates risk by 1 level."""
    # Base LOW + Night -> MEDIUM
    res_night_low = compute_risk('elephant', 0.70, is_night=True, repeat_sighting=False)
    assert res_night_low['risk'] == 'MEDIUM'

    # Base MEDIUM + Night -> HIGH
    res_night_med = compute_risk('elephant', 0.88, is_night=True, repeat_sighting=False)
    assert res_night_med['risk'] == 'HIGH'

def test_risk_elephant_repeat_elevation():
    """Repeat sighting within 30 minutes elevates risk by 1 level."""
    # Base LOW + Repeat -> MEDIUM
    res_rep_low = compute_risk('elephant', 0.70, is_night=False, repeat_sighting=True)
    assert res_rep_low['risk'] == 'MEDIUM'

    # Base MEDIUM + Repeat -> HIGH
    res_rep_med = compute_risk('elephant', 0.88, is_night=False, repeat_sighting=True)
    assert res_rep_med['risk'] == 'HIGH'

def test_risk_elephant_cap_high():
    """Base MEDIUM + Night + Repeat sighting should cap at HIGH."""
    res_cap = compute_risk('elephant', 0.95, is_night=True, repeat_sighting=True)
    assert res_cap['risk'] == 'HIGH'

def test_risk_elephant_review_needed():
    """Elephant detection with confidence < 0.60 must flag review_needed=True."""
    res_review = compute_risk('elephant', 0.55, is_night=False, repeat_sighting=False)
    assert res_review['review_needed']
    assert res_review['risk'] == 'LOW'
