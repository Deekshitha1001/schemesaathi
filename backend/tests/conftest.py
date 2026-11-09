import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.service import SchemeService  # noqa: E402


@pytest.fixture(scope="session")
def service():
    """One service (and one retrieval index) shared by all tests; no LLM."""
    return SchemeService(Settings(llm_provider="none"))
