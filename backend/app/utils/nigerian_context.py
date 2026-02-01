"""Nigerian context and slang utilities."""

from typing import List, Dict

# Common Nigerian Pidgin and slang terms
NIGERIAN_SLANG: Dict[str, str] = {
    # Pidgin expressions
    "na wa": "expression of surprise or disbelief",
    "e no easy": "it's not easy / tough situation",
    "omo": "exclamation (like 'dude' or 'wow')",
    "abeg": "please / I beg",
    "wahala": "trouble / problem",
    "gist": "gossip / story",
    "jara": "bonus / extra",
    "kolo": "crazy / mad",
    "yawa": "trouble / problem",
    "sabi": "know / understand",
    "chop": "eat / enjoy",
    "vex": "angry / annoyed",
    "sharp": "quick / smart",
    "cruise": "fun / joke",
    "gbas gbos": "back and forth exchange / drama",
    "wetin": "what",
    "dey": "is / are / be",
    "no be": "is not / it's not",
    "sha": "anyway / though",
    "sef": "self / even",
    "o": "emphasis particle",
    "las las": "at the end of the day",
    "e choke": "it's overwhelming / impressive",
    "soro soke": "speak up",
    "japa": "run away / emigrate",
    "aza": "bank account / money transfer",

    # Internet/Gen Z slang
    "slay": "look good / succeed",
    "stan": "super fan",
    "ship": "support a relationship",
    "periodt": "period / end of discussion",
    "tea": "gossip",
    "drag": "criticize harshly",
    "shade": "subtle insult",
    "receipts": "evidence / proof",
}

# Common positive expressions
POSITIVE_INDICATORS: List[str] = [
    "slay", "queen", "king", "icon", "legend",
    "❤️", "🔥", "💯", "😍", "👏", "🙌",
    "love", "beautiful", "amazing", "wow",
    "proud", "support", "respect", "talent",
]

# Common negative indicators
NEGATIVE_INDICATORS: List[str] = [
    "fake", "fraud", "scam", "shame",
    "disgusting", "terrible", "worst",
    "hate", "trash", "rubbish",
]


def is_pidgin(text: str) -> bool:
    """
    Check if text likely contains Nigerian Pidgin.

    Args:
        text: Text to check

    Returns:
        True if text appears to contain Pidgin
    """
    text_lower = text.lower()

    pidgin_markers = [
        " dey ", " no be ", " wetin ", " abeg ",
        " omo ", " sha ", " sef ", " na ",
    ]

    for marker in pidgin_markers:
        if marker in f" {text_lower} ":
            return True

    return False


def get_common_slang() -> Dict[str, str]:
    """
    Get dictionary of common Nigerian slang with meanings.

    Returns:
        Dict mapping slang terms to their meanings
    """
    return NIGERIAN_SLANG.copy()


def extract_slang_terms(text: str) -> List[str]:
    """
    Extract recognized slang terms from text.

    Args:
        text: Text to analyze

    Returns:
        List of recognized slang terms found in text
    """
    text_lower = text.lower()
    found = []

    for term in NIGERIAN_SLANG:
        if term in text_lower:
            found.append(term)

    return found


def get_sentiment_hints(text: str) -> Dict[str, int]:
    """
    Get sentiment hints based on Nigerian context.

    Args:
        text: Text to analyze

    Returns:
        Dict with 'positive' and 'negative' counts
    """
    text_lower = text.lower()

    positive_count = sum(
        1 for indicator in POSITIVE_INDICATORS
        if indicator.lower() in text_lower
    )

    negative_count = sum(
        1 for indicator in NEGATIVE_INDICATORS
        if indicator.lower() in text_lower
    )

    return {
        "positive": positive_count,
        "negative": negative_count,
    }
