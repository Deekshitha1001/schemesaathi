"""Extractor behaviour. Several tests are regressions for bugs found by the evaluation sets."""
import sys
from pathlib import Path

import pytest

from app.extract import extract_age, extract_income, extract_profile, normalize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
import eval_extraction  # noqa: E402


def prof(text):
    return extract_profile(text)["profile"]


def test_basic_english_profile():
    p = prof("I am a 45 year old farmer woman from a village in Karnataka. I own 2 acres of land and have a bank account.")
    assert p["age"] == 45 and p["gender"] == "female" and p["occupation"] == "farmer"
    assert p["state"] == "karnataka" and p["area"] == "rural"
    assert p["owns_agri_land"] is True and p["has_bank_account"] is True


def test_silence_is_unknown_never_false():
    assert prof("I am 30 years old.") == {"age": 30}


@pytest.mark.parametrize("text,field", [
    ("I have no bank account", "has_bank_account"),
    ("मेरा बैंक खाता नहीं है", "has_bank_account"),
    ("ನನಗೆ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಲ್ಲ", "has_bank_account"),
    ("I don't pay any income tax", "pays_income_tax"),
    ("ನಾನು ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸುವುದಿಲ್ಲ", "pays_income_tax"),   # regression: Kannada negative verb ending
])
def test_negation_gives_false(text, field):
    assert prof(text)[field] is False


def test_negation_does_not_leak_across_a_comma():
    # regression: "आयकर नहीं देता" used to make the bank account False
    p = prof("मेरे पास बैंक खाता है, आयकर नहीं देता।")
    assert p["has_bank_account"] is True and p["pays_income_tax"] is False


@pytest.mark.parametrize("text", [
    "I am 24, a student. My father is a government employee.",
    "पिताजी सरकारी कर्मचारी हैं। मैं बेरोजगार हूं।",
    "ನನ್ನ ಪತಿ ಸರ್ಕಾರಿ ನೌಕರ. ನಾನು ಗೃಹಿಣಿ.",
])
def test_facts_about_relatives_are_not_the_speakers(text):
    p = prof(text)
    assert "govt_employee" not in p       # regression: used to be True
    assert p.get("occupation") != "salaried"


def test_a_spouses_income_tax_still_counts_but_a_fathers_does_not():
    assert prof("My wife pays income tax.")["pays_income_tax"] is True
    assert "pays_income_tax" not in prof("My father pays income tax.")


def test_own_fact_after_a_relative_is_still_found():
    p = prof("My father has a bank account. I have a bank account too.")
    assert p["has_bank_account"] is True


@pytest.mark.parametrize("text,age", [
    ("I am 33", 33),
    ("My daughter is 6 years old and I am 32.", 32),
    ("I have 20 years of farming experience. I am 50 years old.", 50),
    ("मेरी 8 साल की बेटी है। मैं 36 साल की हूं।", 36),            # regression
    ("My mother is 70. I am her son, 38 years old.", 38),          # regression
    ("ನನಗೆ ೪೫ ವರ್ಷ", 45),                                          # Kannada digits
    ("मैं २२ साल का हूं", 22),                                       # Devanagari digits
])
def test_speakers_own_age(text, age):
    assert extract_age(normalize(text)) == age


def test_age_is_never_a_childs_age():
    assert "age" not in prof("My daughter is 6 years old.")


@pytest.mark.parametrize("text,expected", [
    ("My son is 8 and my daughter is 3.", True),                   # regression: bare number
    ("My daughter is 12 years old.", False),
    ("ನನ್ನ ಮಗಳಿಗೆ 5 ವರ್ಷ", True),
    ("मेरी बेटी 7 साल की है", True),
    ("My daughter is 8 months old", True),
])
def test_girl_child_under_10(text, expected):
    assert prof(text)["girl_child_under_10"] is expected


def test_daughters_age_does_not_cross_sentences():
    # regression: "बेटी है। मैं 36 साल" used to read the mother's 36 as the daughter's age
    assert prof("मेरी 8 साल की बेटी है। मैं 36 साल की हूं।")["girl_child_under_10"] is True


@pytest.mark.parametrize("text,annual", [
    ("My income is 15000 per month", 180000),
    ("Family income is 80,000 per year", 80000),
    ("Our income is 2 lakh", 200000),
    ("income 1.5 lakh a year", 150000),
    ("महीने में 8000 रुपये कमाता हूं", 96000),
    ("परिवार की आय 50,000 रुपये साल में है", 50000),             # regression: "रुपये साल" is a period, not an age
    ("ತಿಂಗಳಿಗೆ 10000 ರೂಪಾಯಿ ಆದಾಯ", 120000),
    ("ಮನೆಯ ವಾರ್ಷಿಕ ಆದಾಯ 1 ಲಕ್ಷ", 100000),
])
def test_income_is_converted_to_a_year(text, annual):
    assert extract_income(normalize(text))[0] == annual


def test_ambiguous_income_is_not_guessed():
    value, warning = extract_income(normalize("my income is 5000"))
    assert value is None and warning == "income_period_unclear"


def test_daily_wage_is_not_converted():
    value, warning = extract_income(normalize("रोज 300 रुपये कमाते हैं"))
    assert value is None and warning == "income_daily"


def test_age_is_not_mistaken_for_income():
    assert extract_income(normalize("I am 45 years old and earn 20000 per month"))[0] == 240000


def test_gender_from_hindi_verb_forms():
    assert prof("मैं किसान हूं और गांव में रहता हूं")["gender"] == "male"
    assert prof("मैं गांव में रहती हूं")["gender"] == "female"


def test_weaver_is_an_artisan_but_not_one_of_the_listed_trades():
    p = prof("मैं बुनकर हूं")
    assert p["occupation"] == "artisan" and "traditional_trade" not in p


def test_every_returned_value_is_valid():
    from app.fields import clean_profile
    p = prof("I am a 45 year old woman, tailor in Bengaluru, income 3 lakh, BPL, own a pucca house")
    assert clean_profile(p) == p


# --- accuracy floors on the evaluation sets (they must not silently get worse) -----------------

def test_dev_set_accuracy_floor():
    report = eval_extraction.run("extraction_cases.json")
    assert report["overall"]["precision"] >= 0.97 and report["overall"]["recall"] >= 0.95


def test_second_set_accuracy_floor():
    report = eval_extraction.run("extraction_heldout.json")
    assert report["overall"]["precision"] >= 0.95 and report["overall"]["recall"] >= 0.93
