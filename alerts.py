"""
alerts.py - Deterministic Risk Logic Engine and Bilingual Alert Message Generator.

NOTE: Risk rules are deterministic domain-specific logic, distinct from the CNN classifier.
"""

from datetime import datetime, time
from common import SITES, RISK_LEVELS

def check_is_night(dt_obj=None, time_mode='auto'):
    """
    Determine if time is considered night (18:00 to 06:00).
    If time_mode is explicit 'day' or 'night', override system clock.
    """
    if time_mode == 'night':
        return True
    if time_mode == 'day':
        return False

    if dt_obj is None:
        dt_obj = datetime.now()

    hour = dt_obj.hour
    return hour >= 18 or hour < 6

def compute_risk(top_class, confidence, is_night, repeat_sighting):
    """
    Calculate risk level according to deterministic safety rules:
    - NONE: If top class is not elephant.
    - If elephant: base = MEDIUM if confidence >= 0.85 else LOW.
    - Raise 1 level if night (18:00-06:00).
    - Raise 1 level if repeat sighting at same site within 30 minutes.
    - Cap at HIGH.
    - Set review_needed = True if elephant confidence < 0.60.
    """
    if top_class != 'elephant':
        return {
            'risk': 'NONE',
            'review_needed': False,
            'repeat_sighting': False,
            'is_night': is_night
        }

    review_needed = confidence < 0.60

    # Determine base risk index (0=NONE, 1=LOW, 2=MEDIUM, 3=HIGH)
    level_idx = 2 if confidence >= 0.85 else 1

    # Apply modifiers
    if is_night:
        level_idx += 1
    if repeat_sighting:
        level_idx += 1

    # Cap at HIGH (index 3)
    level_idx = min(level_idx, 3)
    risk_str = RISK_LEVELS[level_idx]

    return {
        'risk': risk_str,
        'review_needed': review_needed,
        'repeat_sighting': repeat_sighting,
        'is_night': is_night
    }

def generate_alert_text(risk, site_key, time_str, confidence_pct):
    """
    Generate English and Tamil warning alert messages based on risk level.
    NOTE: Tamil text is natural phrasing (flagged for native speaker review).
    """
    site_info = SITES.get(site_key, SITES['maruthamalai'])
    site_name_en = site_info['name']
    site_name_ta = site_info['name_ta']

    if risk == 'NONE':
        en = f"Clear at {site_name_en} ({time_str}). No elephant detected (Confidence: {confidence_pct:.1f}%)."
        ta = f"{site_name_ta} பகுதியில் ({time_str}) யானை நடமாட்டம் இல்லை (உறுதிப்பாடு: {confidence_pct:.1f}%)."
    elif risk == 'LOW':
        en = f"ADVISORY [LOW RISK]: Possible elephant sighting near {site_name_en} at {time_str} ({confidence_pct:.1f}% confidence). Stay vigilant."
        ta = f"அறிவுறுத்தல் [குறைந்த அபாயம்]: {site_name_ta} அருகே {time_str} மணிக்கு யானை இருக்க வாய்ப்புள்ளது (உறுதிப்பாடு: {confidence_pct:.1f}%). எச்சரிக்கையாக இருக்கவும்."
    elif risk == 'MEDIUM':
        en = f"WARNING [MEDIUM RISK]: Elephant detected at {site_name_en} at {time_str} ({confidence_pct:.1f}% confidence). Forest officials & residents notified."
        ta = f"எச்சரிக்கை [நடுத்தர அபாயம்]: {site_name_ta} பகுதியில் {time_str} மணிக்கு யானை கண்டறியப்பட்டது (உறுதிப்பாடு: {confidence_pct:.1f}%). வனத்துறை மற்றும் பொதுமக்களுக்கு அறிவிக்கப்பட்டுள்ளது."
    elif risk == 'HIGH':
        en = f"CRITICAL ALERT [HIGH RISK]: ELEPHANT PRESENCE CONFIRMED at {site_name_en} at {time_str} ({confidence_pct:.1f}% confidence). Immediate caution required! Avoid area."
        ta = f"அவசர எச்சரிக்கை [அதிக அபாயம்]: {site_name_ta} பகுதியில் {time_str} மணிக்கு யானை நடமாட்டம் உறுதி செய்யப்பட்டது (உறுதிப்பாடு: {confidence_pct:.1f}%). உடனடியாக பாதுகாப்பான இடத்திற்கு செல்லவும்!"
    else:
        en = f"Detection logged at {site_name_en} at {time_str}."
        ta = f"{site_name_ta} பகுதியில் {time_str} மணிக்கு பதிவு செய்யப்பட்டது."

    return {'en': en, 'ta': ta}
