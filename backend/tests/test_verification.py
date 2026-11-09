import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.rules import DATA_DIR
from app.verification import mark_verified, parse_date, render_checklist

BACKEND = Path(__file__).resolve().parent.parent


@pytest.fixture()
def data_copy(tmp_path):
    target = tmp_path / "schemes.json"
    shutil.copy(DATA_DIR / "schemes.json", target)
    return target


def test_data_file_round_trips_without_reformatting():
    # mark_verified rewrites the file; it must not create noisy diffs.
    original = (DATA_DIR / "schemes.json").read_text(encoding="utf-8")
    assert json.dumps(json.loads(original), ensure_ascii=False, indent=2) + "\n" == original


def test_mark_verified_sets_date_and_note_for_only_the_named_schemes(data_copy):
    mark_verified(["pm_kisan", "pmuy"], "2026-10-01", note="checked official FAQ", path=data_copy)
    schemes = {s["id"]: s for s in json.loads(data_copy.read_text(encoding="utf-8"))["schemes"]}
    assert schemes["pm_kisan"]["last_verified"] == "2026-10-01" and schemes["pm_kisan"]["verification_notes"] == "checked official FAQ"
    assert schemes["pmuy"]["last_verified"] == "2026-10-01"
    assert not schemes["mudra"].get("last_verified")


def test_unknown_id_changes_nothing(data_copy):
    before = data_copy.read_text(encoding="utf-8")
    with pytest.raises(KeyError):
        mark_verified(["pm_kisan", "no_such_scheme"], "2026-10-01", path=data_copy)
    assert data_copy.read_text(encoding="utf-8") == before


@pytest.mark.parametrize("bad", ["05-11-2026", "yesterday", "2026-13-40", "", "2999-01-01"])
def test_bad_or_future_dates_are_rejected(bad):
    with pytest.raises(ValueError):
        parse_date(bad)


def test_banner_logic_needs_every_scheme_verified(data_copy, monkeypatch):
    """The 'demo data' banner is on until ALL schemes carry a date."""
    ids = [s["id"] for s in json.loads(data_copy.read_text(encoding="utf-8"))["schemes"]]
    mark_verified(ids[:-1], "2026-10-01", path=data_copy)
    assert not all(s.get("last_verified") for s in json.loads(data_copy.read_text(encoding="utf-8"))["schemes"])
    mark_verified(ids[-1:], "2026-10-01", path=data_copy)
    assert all(s.get("last_verified") for s in json.loads(data_copy.read_text(encoding="utf-8"))["schemes"])


def test_checklist_covers_every_scheme_and_its_checks():
    text = render_checklist()
    for scheme in json.loads((DATA_DIR / "schemes.json").read_text(encoding="utf-8"))["schemes"]:
        assert scheme["id"] in text and scheme["source_url"] in text
        assert all(item in text for item in scheme["verify"])
    assert "Progress:" in text and "native speaker" in text


def test_already_confirmed_facts_are_shown_in_the_checklist():
    assert "PIB" in render_checklist()  # the PMJJBY / PMSBY facts confirmed against the PIB release


def test_cli_end_to_end_error_codes():
    run = lambda *a: subprocess.run([sys.executable, str(BACKEND / "scripts" / "mark_verified.py"), *a], capture_output=True, text=True)
    assert run("nope", "--date", "2026-10-01").returncode == 2
    assert run("pm_kisan", "--date", "not-a-date").returncode == 2
    assert run("pm_kisan").returncode == 2  # --date is required
