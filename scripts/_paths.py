import sys
from pathlib import Path


def add_source_directory() -> None:
    """Make production modules importable when a diagnostic runs directly."""
    source_directory = Path(__file__).resolve().parent.parent / "src"
    if str(source_directory) not in sys.path:
        sys.path.insert(0, str(source_directory))
