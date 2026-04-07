from typing import Dict, Iterable, List
import itertools
import os
import requests
import sqlite3
from dotenv import load_dotenv

from ..database.db import upsert_character_voices

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICES_URL = "https://api.elevenlabs.io/v1/voices"

# Cache voices
_VOICE_POOL: List[Dict[str, str]] = []  # {"id": voice_id, "gender": "male|female|neutral"}

# FETCH ONLY API-ALLOWED VOICES (FREE SAFE)

def _fetch_voice_pool() -> List[Dict[str, str]]:
    global _VOICE_POOL

    if _VOICE_POOL:
        return _VOICE_POOL

    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set.")

    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    resp = requests.get(ELEVENLABS_VOICES_URL, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch voices: {resp.status_code} {resp.text}")

    data = resp.json()
    voices = data.get("voices", [])

    pool: List[Dict[str, str]] = []

    for v in voices:
        vid = v.get("voice_id")
        if not vid:
            continue

        labels = v.get("labels") or {}
        gender = str(labels.get("gender", "")).lower()

        if gender not in {"male", "female"}:
            gender = "neutral"

        pool.append({
            "id": vid,
            "gender": gender
        })

    if not pool:
        raise RuntimeError("No usable voices returned by API.")

    _VOICE_POOL = pool
    return _VOICE_POOL

# SIMPLE GENDER INFERENCE

def _infer_gender(name: str) -> str:
    if not name:
        return "neutral"

    lower = name.strip().split()[0].lower()

    female_names = {"meera", "priya", "emma", "olivia", "sophia"}
    male_names = {"raj", "john", "ram", "rahul", "amit"}

    if lower in female_names:
        return "female"

    if lower in male_names:
        return "male"

    if lower.endswith(("a", "i", "e", "y")):
        return "female"

    return "male"

#  MAIN VOICE MAPPING (FREE SAFE)

def ensure_voice_mapping(conn: sqlite3.Connection, speakers: Iterable[str]) -> Dict[str, str]:

    speakers = list({s for s in speakers if s})
    if not speakers:
        return {}

    voices = _fetch_voice_pool()

    male_ids = [v["id"] for v in voices if v["gender"] == "male"]
    female_ids = [v["id"] for v in voices if v["gender"] == "female"]
    neutral_ids = [v["id"] for v in voices if v["gender"] == "neutral"]

    male_cycle = itertools.cycle(male_ids or neutral_ids)
    female_cycle = itertools.cycle(female_ids or neutral_ids)
    neutral_cycle = itertools.cycle(neutral_ids or male_ids or female_ids)

    mapping: Dict[str, str] = {}

    for name in speakers:

        if name.lower() == "narrator":
            mapping[name] = next(neutral_cycle)
            continue

        gender = _infer_gender(name)

        if gender == "female":
            mapping[name] = next(female_cycle)
        elif gender == "male":
            mapping[name] = next(male_cycle)
        else:
            mapping[name] = next(neutral_cycle)

    upsert_character_voices(conn, mapping)
    return mapping