from collections import Counter


SCENE_KEYWORDS = {
    "tense": ["dark", "storm", "thunder", "lightning", "shadow", "fear", "scream", "danger"],
    "happy": ["sunshine", "laugh", "joy", "celebrate", "smile", "bright"],
    "sad": ["cry", "tears", "lonely", "grief", "funeral", "lost"],
    "romantic": ["love", "heart", "kiss", "embrace", "passion"],
    "mysterious": ["unknown", "strange", "whisper", "fog", "silence"],
}


def detect_scene_mood(full_text: str) -> str:
    text = full_text.lower()
    mood_scores = Counter()

    for mood, keywords in SCENE_KEYWORDS.items():
        for word in keywords:
            if word in text:
                mood_scores[mood] += 1

    if not mood_scores:
        return "neutral"

    return mood_scores.most_common(1)[0][0]