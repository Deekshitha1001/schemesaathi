"""The scheme data must stay internally consistent as people edit it."""
from app.fields import FIELD_META, LANGS
from app.rules import load_documents, load_schemes

OPS = {"is_true", "is_false", "eq", "in", "gte", "lte", "between"}


def _rules(scheme):
    for criterion in scheme["criteria"]:
        yield from criterion.get("any_of", [criterion])


def test_ids_are_unique():
    ids = [s["id"] for s in load_schemes()]
    assert len(ids) == len(set(ids))


def test_every_text_is_translated():
    docs = load_documents()
    for scheme in load_schemes():
        for key in ("name", "summary", "benefit", "how_to_apply"):
            assert all(scheme[key].get(lang) for lang in LANGS), (scheme["id"], key)
        for criterion in scheme["criteria"]:
            assert all(criterion["text"].get(lang) for lang in LANGS), scheme["id"]
    for doc_id, text in docs.items():
        assert all(text.get(lang) for lang in LANGS), doc_id


def test_rules_reference_known_fields_and_ops():
    for scheme in load_schemes():
        for rule in _rules(scheme):
            assert rule["field"] in FIELD_META, (scheme["id"], rule["field"])
            assert rule["op"] in OPS, (scheme["id"], rule["op"])


def test_enum_rule_values_are_valid_options():
    for scheme in load_schemes():
        for rule in _rules(scheme):
            meta = FIELD_META[rule["field"]]
            if meta["type"] == "enum":
                values = rule["value"] if isinstance(rule["value"], list) else [rule["value"]]
                assert all(v in meta["options"] for v in values), (scheme["id"], rule)


def test_documents_exist_and_sources_are_https():
    docs = load_documents()
    for scheme in load_schemes():
        assert all(d in docs for d in scheme["documents"]), scheme["id"]
        assert scheme["source_url"].startswith("https://") and scheme["apply_url"].startswith("https://")
        assert scheme["verify"], f"{scheme['id']} has no verification checklist"
