from pydantic import BaseModel
from typing import List, Optional

class SceneResponse(BaseModel):
    scene_number: int
    text: str
    audio_url: str

class UploadResponse(BaseModel):
    id: str
    scenes: List[SceneResponse]
    scene_count: int


class AudioResponse(BaseModel):
    """
    Response returned when requesting an audio file.
    Currently just echoes the id; the actual audio file is streamed.
    """

    id: str
    detail: str = "Audio file stream"


class DialogueSegment(BaseModel):
    """
    Represents a single dialogue/narration segment with an identified speaker.
    """

    speaker: str
    text: str


class CharacterVoice(BaseModel):
    """
    Mapping between a character/speaker and a specific voice id.
    """

    name: str
    voice_id: str

