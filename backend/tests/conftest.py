import pytest
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "documents"


@pytest.fixture
def documents() -> dict[str, str]:
    """Real case documents loaded from disk (used by integration-style tests)."""
    return {p.stem: p.read_text() for p in DOCS.glob("*.txt")}


@pytest.fixture
def motion_text(documents) -> str:
    return documents["motion_for_summary_judgment"]
