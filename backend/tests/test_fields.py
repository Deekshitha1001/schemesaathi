import pytest

from app.fields import FIELD_META, LANGS, clean_profile, clean_value, public_meta


@pytest.mark.parametrize("field,value,expected", [
    ("age", 30, 30), ("age", "30", 30), ("age", 0, None), ("age", 150, None), ("age", -1, None), ("age", "abc", None),
    ("annual_income", 12.5, 12.5), ("annual_income", -1, None),
    ("gender", "female", "female"), ("gender", "alien", None),
    ("has_bank_account", True, True), ("has_bank_account", "false", False), ("has_bank_account", "yes", None), ("has_bank_account", 1, None),
    ("nonsense", 1, None), ("age", None, None), ("age", "", None),
])
def test_clean_value(field, value, expected):
    assert clean_value(field, value) == expected


def test_clean_profile_drops_unknown_and_invalid():
    assert clean_profile({"age": 30, "zzz": 1, "gender": "x"}) == {"age": 30}
    assert clean_profile(None) == {}


def test_every_field_is_fully_translated():
    for name, meta in FIELD_META.items():
        for key in ("label", "question"):
            assert all(meta[key].get(lang) for lang in LANGS), (name, key)
        for option in meta.get("options", {}).values():
            assert all(option.get(lang) for lang in LANGS), name


def test_public_meta_shape():
    meta = public_meta()
    assert meta["order"] == list(FIELD_META) and set(meta["languages"]) == set(LANGS)
