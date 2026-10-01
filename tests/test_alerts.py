"""
tests/test_alerts.py - Unit tests for bilingual English & Tamil alert generation.
"""

from alerts import generate_alert_text

def test_alert_text_none():
    msgs = generate_alert_text('NONE', 'maruthamalai', '14:30', 98.5)
    assert 'Clear' in msgs['en']
    assert 'யானை நடமாட்டம் இல்லை' in msgs['ta']

def test_alert_text_low():
    msgs = generate_alert_text('LOW', 'thadagam', '16:45', 72.0)
    assert 'ADVISORY' in msgs['en']
    assert 'குறைந்த அபாயம்' in msgs['ta']

def test_alert_text_medium():
    msgs = generate_alert_text('MEDIUM', 'anaikatti', '19:15', 88.0)
    assert 'WARNING' in msgs['en']
    assert 'நடுத்தர அபாயம்' in msgs['ta']

def test_alert_text_high():
    msgs = generate_alert_text('HIGH', 'madukkarai', '22:00', 94.0)
    assert 'CRITICAL ALERT' in msgs['en']
    assert 'அவசர எச்சரிக்கை' in msgs['ta']
