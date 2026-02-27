import re
from typing import List, Dict

import spacy

# Load a small English model.
# Make sure to install it with:
#   python -m spacy download en_core_web_sm
_NLP = spacy.load("en_core_web_sm")


def clean_text(text: str) -> str:
    """
    Basic text cleanup: normalize whitespace and remove extra symbols.
    """
    # Replace fancy quotes with standard quotes
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_dialogue_segments(text: str) -> List[Dict[str, str]]:
    """
    Detect dialogue segments using quotation marks and attempt to identify speakers.

    Example handled pattern:
        "Hello," said John.
    Heuristic:
        - Dialogue text is inside quotes.
        - Speaker is the PERSON entity near verbs like 'said', 'asked', 'replied'.
        - If no clear speaker, label as 'narrator'.
    """
    segments: List[Dict[str, str]] = []

    # Roughly split text into sentences using spaCy
    doc = _NLP(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    for sent in sentences:
        # Find quoted parts
        quotes = re.findall(r'"(.*?)"', sent)
        if not quotes:
            # No explicit dialogue, treat as narrator narration
            segments.append(
                {
                    "speaker": "narrator",
                    "text": sent,
                    "emotion": _infer_emotion(sent),
                }
            )
            continue

        # Re-run NLP on sentence for local context
        sent_doc = _NLP(sent)

        # Find candidate speaker name (PERSON entity)
        speaker_name = _find_speaker_name(sent_doc)
        if not speaker_name:
            speaker_name = "narrator"

        for quoted in quotes:
            clean_dialogue = quoted.strip()
            if clean_dialogue:
                segments.append(
                    {
                        "speaker": speaker_name,
                        "text": clean_dialogue,
                        "emotion": _infer_emotion(clean_dialogue),
                    }
                )

    return segments


def _find_speaker_name(doc: spacy.tokens.Doc) -> str:
    """
    Find a likely speaker name in the sentence using spaCy NER and simple patterns.
    """
    # Look for PERSON entities
    person_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    # Target verbs commonly used in dialogue attribution
    dialogue_verbs = {"say", "said", "reply", "replied", "ask", "asked", "shout", "shouted"}

    # Simple heuristic:
    #   If we see pattern like 'said John' or 'John said', assign 'John'
    tokens = list(doc)
    for i, token in enumerate(tokens):
        lower = token.lemma_.lower()
        if lower in dialogue_verbs:
            # Check token after verb: 'said John'
            if i + 1 < len(tokens):
                after = tokens[i + 1].text
                if after in person_entities:
                    return after
            # Check token before verb: 'John said'
            if i - 1 >= 0:
                before = tokens[i - 1].text
                if before in person_entities:
                    return before

    # Fallback: first PERSON entity in sentence
    if person_entities:
        return person_entities[0]

    return ""


def _infer_emotion(text: str) -> str:
    """
    Very lightweight emotion heuristic based on keywords and punctuation.
    Returns one of: 'happy', 'sad', 'angry', 'question', 'neutral'.
    This is intentionally simple to avoid heavy models.
    """
    t = text.lower()

    # Strong cues first
    happy_words = ["happy", "glad", "excited", "love", "wonderful", "great", "awesome"]
    sad_words = ["sad", "upset", "cry", "unhappy", "bad", "terrible", "sorry"]
    angry_words = ["angry", "mad", "furious", "hate", "annoyed", "frustrated"]
    question_marks = "?" in text

    if any(w in t for w in happy_words):
        return "happy"
    if any(w in t for w in sad_words):
        return "sad"
    if any(w in t for w in angry_words):
        return "angry"
    if question_marks:
        return "question"

    # Exclamation often indicates heightened emotion; treat as happy/excited
    if "!" in text:
        return "happy"

    return "neutral"

