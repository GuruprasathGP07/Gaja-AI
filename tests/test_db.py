"""
tests/test_db.py - Unit tests for SQLite database CRUD and 30-minute repeat window queries.
"""

import os
import pytest
from datetime import datetime
import db

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    db.init_db()
    db.clear_db()
    yield
    db.clear_db()

def test_db_insert_and_get_events():
    event_data = {
        'timestamp': datetime.now().isoformat(),
        'site_key': 'maruthamalai',
        'label': 'elephant',
        'confidence': 91.5,
        'risk': 'MEDIUM',
        'is_night': False,
        'review_needed': False,
        'repeat_sighting': False,
        'alert_en': 'Warning elephant detected',
        'alert_ta': 'யானை கண்டறியப்பட்டது',
        'image_url': '/static/uploads/test.jpg',
        'probs': {'elephant': 0.915, 'other_animal': 0.05, 'no_animal': 0.035}
    }

    event_id = db.add_event(event_data)
    assert event_id > 0

    events = db.get_events(limit=10)
    assert len(events) == 1
    assert events[0]['site_key'] == 'maruthamalai'
    assert events[0]['label'] == 'elephant'

def test_db_repeat_sighting_window():
    site_key = 'thadagam'
    # Initially no repeat sighting
    assert not db.check_repeat_sighting(site_key, window_minutes=30)

    # Insert elephant event at site
    event_data = {
        'timestamp': datetime.now().isoformat(),
        'site_key': site_key,
        'label': 'elephant',
        'confidence': 89.0,
        'risk': 'MEDIUM',
        'is_night': False,
        'review_needed': False,
        'repeat_sighting': False,
        'alert_en': 'Alert',
        'alert_ta': 'எச்சரிக்கை',
        'image_url': '/static/uploads/test.jpg',
        'probs': {'elephant': 0.89, 'other_animal': 0.05, 'no_animal': 0.06}
    }
    db.add_event(event_data)

    # Now repeat sighting must be True
    assert db.check_repeat_sighting(site_key, window_minutes=30)

def test_db_stats():
    event_data = {
        'timestamp': datetime.now().isoformat(),
        'site_key': 'anaikatti',
        'label': 'elephant',
        'confidence': 96.0,
        'risk': 'HIGH',
        'is_night': True,
        'review_needed': False,
        'repeat_sighting': True,
        'alert_en': 'High alert',
        'alert_ta': 'அதிக அபாயம்',
        'image_url': '/static/uploads/test2.jpg',
        'probs': {'elephant': 0.96, 'other_animal': 0.02, 'no_animal': 0.02}
    }
    db.add_event(event_data)

    stats = db.get_stats()
    assert stats['total'] == 1
    assert stats['total_elephants'] == 1
    assert stats['total_high'] == 1
    assert len(stats['hourly_sightings']) == 24
    assert stats['sites']['anaikatti']['latest_risk'] == 'HIGH'
