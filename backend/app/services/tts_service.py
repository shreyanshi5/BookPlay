import os
from typing import List, Dict
import requests
from dotenv import load_dotenv

from .scene_service import detect_scene_mood

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")


# Sentence-Level Emotion Detection
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

# Hierarchical Voice Modulation

def _get_voice_settings(emotion: str, scene_mood: str):

    stability = 0.5
    similarity = 0.85
    style = 0.3
    speed = 1.0

    # Scene-level baseline
    if scene_mood == "tense":
        stability += 0.15
        style += 0.35
        speed -= 0.20

    elif scene_mood == "dramatic":
        stability += 0.15
        style += 0.45
        speed -= 0.25

    elif scene_mood == "happy":
        speed += 0.08
        style += 0.12

    elif scene_mood == "sad":
        stability += 0.25
        speed -= 0.18

    elif scene_mood == "romantic":
        speed -= 0.10
        style += 0.18

    elif scene_mood == "mysterious":
        stability += 0.20
        speed -= 0.18

    # Sentence-level override
    if emotion == "excited":
        speed += 0.25
        style += 0.25

    elif emotion == "whisper":
        speed -= 0.25
        style -= 0.1
        stability += 0.1

    elif emotion == "angry":
        style += 0.3
        stability -= 0.2
        speed += 0.1

    elif emotion == "sad":
        speed -= 0.15
        stability += 0.15

    elif emotion == "question":
        style += 0.1
        speed += 0.05

    # ElevenLabs safe limits
    stability = max(0.1, min(1.0, stability))
    style = max(0.0, min(1.0, style))
    speed = max(0.7, min(1.2, speed))

    return {
        "stability": stability,
        "similarity_boost": similarity,
        "style": style,
        "speed": speed,
        "use_speaker_boost": True,
    }


# ElevenLabs API Call

def _synthesize_text(text: str, voice_id: str, emotion: str, scene_mood: str) -> bytes:

    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY environment variable is not set.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": _get_voice_settings(emotion, scene_mood),
    }

    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id) + f"?output_format={ELEVENLABS_OUTPUT_FORMAT}"

    print("Calling ElevenLabs...")
    print("Text length:", len(text))

    response = requests.post(url, json=payload, headers=headers)

    print("Status Code:", response.status_code)
    print("Returned Bytes:", len(response.content))

    if response.status_code != 200:
        print("Error Response:", response.text)
        raise RuntimeError(f"ElevenLabs API error {response.status_code}: {response.text}")

    return response.content


# Main Scene-Based Audio Generator

def generate_narration_audio(
    segments: List[Dict[str, str]],
    voice_mapping: Dict[str, str],
    output_path: str,
) -> None:

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Detect Scene Mood Once Per Scene
    full_text = " ".join([seg["text"] for seg in segments])
    scene_mood = detect_scene_mood(full_text)

    with open(output_path, "wb") as out_f:

        for seg in segments:

            speaker = seg.get("speaker", "narrator")
            text = seg.get("text", "").strip()

            if not text:
                continue

            voice_id = voice_mapping.get(speaker) or voice_mapping.get("narrator")

            if not voice_id:
                raise RuntimeError(f"No voice mapping found for speaker '{speaker}'.")

            emotion = _detect_emotion(text)

            audio_bytes = _synthesize_text(
                text=text,
                voice_id=voice_id,
                emotion=emotion,
                scene_mood=scene_mood,
            )

            out_f.write(audio_bytes)

            # Cinematic Pause Control
            pause_length = 6000  # default micro pause

            if scene_mood in ["tense", "dramatic"]:
                pause_length = 14000
            elif scene_mood == "happy":
                pause_length = 4000
            elif scene_mood == "sad":
                pause_length = 10000
            elif scene_mood == "mysterious":
                pause_length = 12000

            out_f.write(b"\x00" * pause_length)