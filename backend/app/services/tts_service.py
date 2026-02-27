import os
from typing import List, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")


# ==========================================================
# 🎭 SMART EMOTION DETECTION
# ==========================================================

def _detect_emotion(text: str) -> str:
    lower = text.lower().strip()

    if "whisper" in lower or lower.endswith("..."):
        return "whisper"

    if "shouted" in lower or "yelled" in lower or "!" in text:
        return "excited"

    if "angrily" in lower or "furious" in lower:
        return "angry"

    if "sadly" in lower or "cried" in lower:
        return "sad"

    if "laughed" in lower or "happily" in lower:
        return "happy"

    if text.endswith("?"):
        return "question"

    return "neutral"


# ==========================================================
# 🎛 VOICE PARAMETER TUNING
# ==========================================================

def _get_voice_settings(emotion: str):

    # Default baseline
    stability = 0.50
    similarity = 0.85
    style = 0.30
    speed = 1.00

    if emotion == "angry":
        stability = 0.18
        style = 0.85
        speed = 1.08

    elif emotion == "sad":
        stability = 0.75
        style = 0.20
        speed = 0.90

    elif emotion == "happy":
        stability = 0.30
        style = 0.65
        speed = 1.05

    elif emotion == "excited":
        stability = 0.22
        style = 0.90
        speed = 1.10

    elif emotion == "whisper":
        stability = 0.65
        style = 0.10
        speed = 0.92

    elif emotion == "question":
        stability = 0.45
        style = 0.40
        speed = 1.02

    return {
        "stability": stability,
        "similarity_boost": similarity,
        "style": style,
        "speed": speed,
        "use_speaker_boost": True,
    }


# ==========================================================
# 🔊 TTS CALL
# ==========================================================

def _synthesize_text(
    text: str,
    voice_id: str,
    emotion: str,
) -> bytes:

    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY environment variable is not set.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": _get_voice_settings(emotion),
    }

    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id) + f"?output_format={ELEVENLABS_OUTPUT_FORMAT}"

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error {response.status_code}: {response.text}")

    return response.content


# ==========================================================
# 🎬 MAIN AUDIO GENERATOR
# ==========================================================

def generate_narration_audio(
    segments: List[Dict[str, str]],
    voice_mapping: Dict[str, str],
    output_path: str,
) -> None:

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as out_f:

        for seg in segments:

            speaker = seg.get("speaker", "narrator")
            text = seg.get("text", "").strip()

            if not text:
                continue

            voice_id = voice_mapping.get(speaker) or voice_mapping.get("narrator")

            if not voice_id:
                raise RuntimeError(f"No voice mapping found for speaker '{speaker}'.")

            # 🔥 Automatic emotion detection
            emotion = _detect_emotion(text)

            audio_bytes = _synthesize_text(
                text=text,
                voice_id=voice_id,
                emotion=emotion,
            )

            out_f.write(audio_bytes)

            # 🎬 Cinematic micro pause (~200ms feel)
            out_f.write(b"\x00" * 6000)