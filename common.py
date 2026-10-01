"""
common.py - Common definitions, camera site metadata, and configuration constants.
"""

import os

# Classes mapping
CLASSES = ['elephant', 'other_animal', 'no_animal']
CLASS_NAMES_EN = {
    'elephant': 'Elephant',
    'other_animal': 'Other Animal',
    'no_animal': 'No Animal'
}

CLASS_NAMES_TA = {
    'elephant': 'யானை',
    'other_animal': 'மற்ற விலங்கு',
    'no_animal': 'விலங்கு இல்லை'
}

# State-Wide Elephant Conflict Surveillance Stations across Tamil Nadu
SITES = {
    'maruthamalai': {
        'key': 'maruthamalai',
        'name': 'Maruthamalai Foothills (Coimbatore)',
        'name_ta': 'மருதமலை അടിவாரம் (கோயம்புத்தூர்)',
        'lat': 11.0450,
        'lon': 76.9025,
        'sector': 'Coimbatore Range',
        'location_desc': 'Maruthamalai Forest Edge, Coimbatore Range'
    },
    'thadagam': {
        'key': 'thadagam',
        'name': 'Thadagam Valley (Coimbatore)',
        'name_ta': 'தடாகம் பள்ளத்தாக்கு (கோயம்புத்தூர்)',
        'lat': 11.0833,
        'lon': 76.8833,
        'sector': 'Coimbatore Range',
        'location_desc': 'Thadagam Brick Kiln Migratory Corridor'
    },
    'anaikatti': {
        'key': 'anaikatti',
        'name': 'Anaikatti Hill Pass (Coimbatore)',
        'name_ta': 'ஆனைக்கட்டி கணவாய் (கோயம்புத்தூர்)',
        'lat': 11.1020,
        'lon': 76.7740,
        'sector': 'Coimbatore Range',
        'location_desc': 'Anaikatti Interstate Hill Pass Road'
    },
    'boluvampatti': {
        'key': 'boluvampatti',
        'name': 'Boluvampatti Sanctuary Gate (Coimbatore)',
        'name_ta': 'போளுவாம்பட்டி வனக் கதவு (கோயம்புத்தூர்)',
        'lat': 10.9333,
        'lon': 76.7500,
        'sector': 'Coimbatore Range',
        'location_desc': 'Boluvampatti Reserve Forest Sanctuary Gate'
    },
    'gudalur': {
        'key': 'gudalur',
        'name': 'Gudalur Forest Zone (Nilgiris)',
        'name_ta': 'கூடலூர் வன மண்டலம் (நீலகிரி)',
        'lat': 11.5000,
        'lon': 76.4900,
        'sector': 'Nilgiris Division',
        'location_desc': 'Gudalur Division, Nilgiris Border'
    },
    'masinagudi': {
        'key': 'masinagudi',
        'name': 'Masinagudi Corridor (Mudumalai STR)',
        'name_ta': 'மசினகுடி பாதை (முதுமலை மண்டலம்)',
        'lat': 11.5722,
        'lon': 76.6439,
        'sector': 'Mudumalai Tiger Reserve',
        'location_desc': 'Mudumalai Tiger Reserve Elephant Pass'
    },
    'sanamavu': {
        'key': 'sanamavu',
        'name': 'Sanamavu Reserve Forest (Hosur/Krishnagiri)',
        'name_ta': 'சனமாவு காப்புக்காடு (ஓசூர்/கிருஷ்ணகிரி)',
        'lat': 12.6350,
        'lon': 77.9250,
        'sector': 'Hosur/Krishnagiri Division',
        'location_desc': 'Hosur Division Elephant Sanctuary Corridor'
    },
    'denkanikottai': {
        'key': 'denkanikottai',
        'name': 'Denkanikottai Range (Hosur)',
        'name_ta': 'டென்கனிக்கோட்டை வனப்பகுதி (ஓசூர்)',
        'lat': 12.5270,
        'lon': 77.7910,
        'sector': 'Hosur Division',
        'location_desc': 'Denkanikottai Interstate Migration Route'
    },
    'valparai': {
        'key': 'valparai',
        'name': 'Valparai Plateau (Anamalai ATR)',
        'name_ta': 'வால்பாறை பீடபூமி (ஆனைமலை)',
        'lat': 10.3267,
        'lon': 76.9553,
        'sector': 'Anamalai Tiger Reserve',
        'location_desc': 'Valparai Tea Estate Elephant Corridor'
    },
    'sathyamangalam': {
        'key': 'sathyamangalam',
        'name': 'Sathyamangalam STR (Erode)',
        'name_ta': 'சத்தியமங்கலம் புலிகள் காப்பகம் (ஈரோடு)',
        'lat': 11.5050,
        'lon': 77.2400,
        'sector': 'Sathyamangalam STR',
        'location_desc': 'Sathyamangalam Highway Migration Crossing'
    },
    'hasanur': {
        'key': 'hasanur',
        'name': 'Hasanur Range (Sathyamangalam)',
        'name_ta': 'ஹாசனூர் வனச்சரகம் (சத்தியமங்கலம்)',
        'lat': 11.7580,
        'lon': 77.0650,
        'sector': 'Sathyamangalam STR',
        'location_desc': 'Hasanur Ghat Road Wildlife Zone'
    },
    'pennagaram': {
        'key': 'pennagaram',
        'name': 'Pennagaram Reserve Forest (Dharmapuri)',
        'name_ta': 'பெண்ணாகரம் காப்புக்காடு (தருமபுரி)',
        'lat': 12.1333,
        'lon': 77.9000,
        'sector': 'Dharmapuri Division',
        'location_desc': 'Cauvery Wildlife Sanctuary Border, Dharmapuri'
    },
    'madukkarai': {
        'key': 'madukkarai',
        'name': 'Madukkarai Railway Fringe (Coimbatore)',
        'name_ta': 'மடுக்கரை இரயில்வே எல்லை (கோயம்புத்தூர்)',
        'lat': 10.9050,
        'lon': 76.9550,
        'sector': 'Coimbatore Division',
        'location_desc': 'Madukkarai Railway Track Wildlife Crossing'
    },
    'megamalai': {
        'key': 'megamalai',
        'name': 'Megamalai Wildlife Zone (Theni)',
        'name_ta': 'மேகமலை வனவிலங்கு மண்டலம் (தேனி)',
        'lat': 9.6955,
        'lon': 77.4042,
        'sector': 'Theni/Megamalai Division',
        'location_desc': 'Srivilliputhur-Megamalai Corridor'
    }
}

DEFAULT_SITE = 'maruthamalai'

# Risk levels
RISK_LEVELS = ['NONE', 'LOW', 'MEDIUM', 'HIGH']

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')
MODEL_PATH = os.path.join(MODEL_DIR, 'gajaalert_model.keras')
BASELINE_MODEL_PATH = os.path.join(MODEL_DIR, 'baseline_model.keras')
LABELS_PATH = os.path.join(MODEL_DIR, 'labels.json')
META_PATH = os.path.join(MODEL_DIR, 'gajaalert_model.meta.json')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
METRICS_PATH = os.path.join(RESULTS_DIR, 'metrics.json')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'gajaalert.db')
