import re


PREFERENCE_PATTERNS = (
    (
        "cultural activities",
        re.compile(r"\bcultural activit(?:y|ies)\b", re.IGNORECASE),
    ),
    ("food", re.compile(r"\bfood\b", re.IGNORECASE)),
    (
        "outdoor activities",
        re.compile(r"\boutdoor activit(?:y|ies)\b", re.IGNORECASE),
    ),
    (
        "indoor activities",
        re.compile(r"\bindoor activit(?:y|ies)\b", re.IGNORECASE),
    ),
    (
        "nature / wildlife",
        re.compile(r"\b(?:nature|wildlife)\b", re.IGNORECASE),
    ),
    ("shopping", re.compile(r"\bshopping\b", re.IGNORECASE)),
)


def extract_preferences(text: str) -> list[str]:
    """Extract supported travel preferences in the order they appear in text."""
    matches = [
        (match.start(), preference)
        for preference, pattern in PREFERENCE_PATTERNS
        if (match := pattern.search(text)) is not None
    ]
    return [preference for _, preference in sorted(matches)]


if __name__ == "__main__":
    test_inputs = (
        "I prefer cultural activities and food for my Singapore trip.",
        "I enjoy outdoor activities and wildlife.",
        "I want indoor activities and shopping.",
    )

    for text in test_inputs:
        print(f"Input: {text}")
        print(f"Preferences: {extract_preferences(text)}\n")
