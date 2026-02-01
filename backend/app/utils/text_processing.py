"""Text processing utilities."""


def anonymize_username(username: str) -> str:
    """
    Anonymize username with asterisks for privacy.

    Examples:
        'johndoe123' -> 'joh***123'
        'user' -> 'u***'
        'ab' -> 'a***'

    Args:
        username: Original username

    Returns:
        Anonymized username
    """
    if not username:
        return "***"

    if len(username) <= 4:
        return username[0] + "***"

    visible_start = max(1, len(username) // 3)
    visible_end = max(1, len(username) // 3)

    middle_length = len(username) - visible_start - visible_end

    return (
        username[:visible_start]
        + "*" * middle_length
        + username[-visible_end:]
    )


def truncate_text(text: str, max_length: int = 150, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding suffix if truncated.

    Args:
        text: Original text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)].rstrip() + suffix


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.

    Args:
        text: Original text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = " ".join(text.split())

    return text.strip()


def censor_profanity(text: str, replacement: str = "***") -> str:
    """
    Censor known profanity in text.

    This is a basic implementation - consider using a proper
    profanity filter library for production.

    Args:
        text: Original text
        replacement: Replacement string for profanity

    Returns:
        Censored text
    """
    # Basic profanity list - extend as needed
    profanity = [
        # Add words to censor here
    ]

    result = text
    for word in profanity:
        # Case-insensitive replacement
        import re

        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(replacement, result)

    return result
