"""
db.py - SQLite database module for event logging, statistics, and 30-minute repeat window checks.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from common import DB_PATH, SITES

def get_db_connection():
    """Establish and return SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            site_key TEXT NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk TEXT NOT NULL,
            is_night INTEGER NOT NULL DEFAULT 0,
            review_needed INTEGER NOT NULL DEFAULT 0,
            repeat_sighting INTEGER NOT NULL DEFAULT 0,
            alert_en TEXT NOT NULL,
            alert_ta TEXT NOT NULL,
            image_url TEXT NOT NULL,
            probs_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def check_repeat_sighting(site_key, window_minutes=30):
    """
    Check if an elephant was detected at the specified site within the last window_minutes.
    Returns True if an elephant detection exists in the time window.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff_dt = datetime.now() - timedelta(minutes=window_minutes)
    cutoff_str = cutoff_dt.isoformat()

    cursor.execute('''
        SELECT COUNT(*) as cnt FROM detection_events
        WHERE site_key = ? AND label = 'elephant' AND timestamp >= ?
    ''', (site_key, cutoff_str))

    row = cursor.fetchone()
    conn.close()
    return row['cnt'] > 0 if row else False

def add_event(event):
    """Insert a new detection event into the database and return event ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    ts = event.get('timestamp', datetime.now().isoformat())
    probs_json = json.dumps(event.get('probs', {}))

    cursor.execute('''
        INSERT INTO detection_events (
            timestamp, site_key, label, confidence, risk,
            is_night, review_needed, repeat_sighting,
            alert_en, alert_ta, image_url, probs_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ts,
        event['site_key'],
        event['label'],
        float(event['confidence']),
        event['risk'],
        1 if event['is_night'] else 0,
        1 if event['review_needed'] else 0,
        1 if event['repeat_sighting'] else 0,
        event['alert_en'],
        event['alert_ta'],
        event['image_url'],
        probs_json
    ))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_events(limit=50):
    """Fetch latest detection events sorted by timestamp descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM detection_events ORDER BY id DESC LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    events = []
    for r in rows:
        d = dict(r)
        d['site'] = SITES.get(d['site_key'], SITES['maruthamalai'])
        d['probs'] = json.loads(d['probs_json']) if d.get('probs_json') else {}
        d['is_night'] = bool(d['is_night'])
        d['review_needed'] = bool(d['review_needed'])
        d['repeat_sighting'] = bool(d['repeat_sighting'])
        events.append(d)

    return events

def get_stats():
    """
    Compute aggregate statistics:
    - Total detections
    - Total elephant detections
    - Total high risk alerts
    - Sightings by hour (24-element array for today)
    - Latest risk status per site
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Totals
    cursor.execute('SELECT COUNT(*) as total FROM detection_events')
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total_elephants FROM detection_events WHERE label = 'elephant'")
    total_elephants = cursor.fetchone()['total_elephants']

    cursor.execute("SELECT COUNT(*) as total_high FROM detection_events WHERE risk = 'HIGH'")
    total_high = cursor.fetchone()['total_high']

    # Hourly counts (24-hour histogram)
    hourly = [0] * 24
    cursor.execute("SELECT timestamp FROM detection_events WHERE label = 'elephant'")
    for r in cursor.fetchall():
        try:
            dt = datetime.fromisoformat(r['timestamp'])
            hourly[dt.hour] += 1
        except Exception:
            pass

    # Latest status per site
    site_status = {}
    for sk, sinfo in SITES.items():
        cursor.execute('''
            SELECT risk, timestamp, label, confidence FROM detection_events
            WHERE site_key = ? ORDER BY id DESC LIMIT 1
        ''', (sk,))
        row = cursor.fetchone()
        if row:
            site_status[sk] = {
                'key': sk,
                'name': sinfo['name'],
                'lat': sinfo['lat'],
                'lon': sinfo['lon'],
                'latest_risk': row['risk'],
                'latest_label': row['label'],
                'latest_confidence': row['confidence'],
                'timestamp': row['timestamp']
            }
        else:
            site_status[sk] = {
                'key': sk,
                'name': sinfo['name'],
                'lat': sinfo['lat'],
                'lon': sinfo['lon'],
                'latest_risk': 'NONE',
                'latest_label': 'no_animal',
                'latest_confidence': 100.0,
                'timestamp': None
            }

    conn.close()

    return {
        'total': total,
        'total_elephants': total_elephants,
        'total_high': total_high,
        'hourly_sightings': hourly,
        'sites': site_status
    }

def clear_db():
    """Clear all records from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM detection_events')
    conn.commit()
    conn.close()
