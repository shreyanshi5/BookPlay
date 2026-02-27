def detect_emotion(text: str) -> str:
    """
    Rule-based lightweight emotion detection.
    """

    lower = text.lower().strip()

    if "whisper" in lower:
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