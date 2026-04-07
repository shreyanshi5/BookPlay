import re
from typing import List


SCENE_TRANSITION_PATTERNS = [
    r"\bthe next day\b",
    r"\bthe next morning\b",
    r"\bthe next evening\b",
    r"\blater that night\b",
    r"\blater that evening\b",
    r"\blater that day\b",
    r"\bat dawn\b",
    r"\bat sunrise\b",
    r"\bhours later\b",
    r"\bmeanwhile\b",
]


def split_into_scenes(text: str) -> List[str]:
    """
    Split text into scenes based on:
    - Explicit separator lines (e.g., _______)
    - Double line breaks
    - Strong time transition keywords
    """

    # Normalize line breaks
    text = text.replace("\r", "")

    # Split on visual separator lines
    text = re.sub(r"\n_{3,}\n", "\n\n<SPLIT>\n\n", text)

    # Split on strong time transitions
    for pattern in SCENE_TRANSITION_PATTERNS:
        text = re.sub(
            pattern,
            lambda match: "\n\n<SPLIT>\n\n" + match.group(0),
            text,
            flags=re.IGNORECASE
        )
    # Final split
    parts = [p.strip() for p in text.split("<SPLIT>") if p.strip()]

    return parts