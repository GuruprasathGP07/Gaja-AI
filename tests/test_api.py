"""
tests/test_api.py - Unit tests for Flask REST API endpoints and error paths.
"""

import io
import json
import pytest
from PIL import Image
from app import app
import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        db.init_db()
        db.clear_db()
        yield client
        db.clear_db()

def create_test_image_bytes():
    """Create synthetic PNG image bytes for testing upload."""
    img = Image.new('RGB', (100, 100), color='green')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def test_health_endpoint(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'OK'

def test_predict_happy_path(client):
    img_bytes = create_test_image_bytes()
    data = {
        'image': (img_bytes, 'test_elephant.png'),
        'site': 'maruthamalai',
        'time_mode': 'day'
    }
    res = client.post('/predict', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    json_data = res.get_json()
    assert 'id' in json_data
    assert 'risk' in json_data
    assert json_data['site']['key'] == 'maruthamalai'
    assert 'alert_en' in json_data
    assert 'alert_ta' in json_data

def test_predict_missing_image(client):
    res = client.post('/predict', data={}, content_type='multipart/form-data')
    assert res.status_code == 400
    json_data = res.get_json()
    assert 'error' in json_data

def test_predict_bad_file_format(client):
    bad_bytes = io.BytesIO(b"not an image file content")
    data = {
        'image': (bad_bytes, 'corrupt.txt'),
        'site': 'maruthamalai'
    }
    res = client.post('/predict', data=data, content_type='multipart/form-data')
    assert res.status_code == 400
    json_data = res.get_json()
    assert 'error' in json_data

def test_api_events_and_stats(client):
    # Predict first
    img_bytes = create_test_image_bytes()
    client.post('/predict', data={'image': (img_bytes, 'sample.jpg'), 'site': 'anaikatti'}, content_type='multipart/form-data')

    # Get events
    res_ev = client.get('/api/events')
    assert res_ev.status_code == 200
    assert len(res_ev.get_json()['events']) == 1

    # Get stats
    res_st = client.get('/api/stats')
    assert res_st.status_code == 200
    assert res_st.get_json()['total'] == 1

def test_clear_events_restricted(client):
    res = client.post('/api/clear')
    assert res.status_code in [200, 403]
