import pytest

from app.rules import check_criterion, check_rule, evaluate_all, evaluate_scheme, next_questions, scheme_by_id


def status(scheme_id, profile):
    return evaluate_scheme(scheme_by_id(scheme_id), profile)["status"]


def test_rule_ops():
    assert check_rule({"field": "age", "op": "between", "value": [18, 40]}, {"age": 18}) == "pass"
    assert check_rule({"field": "age", "op": "between", "value": [18, 40]}, {"age": 41}) == "fail"
    assert check_rule({"field": "age", "op": "gte", "value": 60}, {"age": 60}) == "pass"
    assert check_rule({"field": "age", "op": "lte", "value": 60}, {"age": 61}) == "fail"
    assert check_rule({"field": "gender", "op": "eq", "value": "female"}, {"gender": "male"}) == "fail"
    assert check_rule({"field": "ration_card", "op": "in", "value": ["bpl"]}, {"ration_card": "bpl"}) == "pass"
    assert check_rule({"field": "has_bank_account", "op": "is_true"}, {"has_bank_account": False}) == "fail"
    assert check_rule({"field": "pays_income_tax", "op": "is_false"}, {"pays_income_tax": False}) == "pass"


def test_missing_value_is_unknown_not_fail():
    assert check_rule({"field": "age", "op": "gte", "value": 60}, {}) == "unknown"


def test_soft_rule_never_gives_a_hard_pass():
    rule = {"field": "ration_card", "op": "in", "value": ["bpl"], "soft": True}
    assert check_rule(rule, {"ration_card": "bpl"}) == "soft"
    assert check_rule(rule, {"ration_card": "apl"}) == "fail"


def test_any_of_takes_the_best_alternative():
    pm_jay = scheme_by_id("pm_jay")["criteria"][0]
    assert check_criterion(pm_jay, {"age": 72})[0] == "pass"                       # senior: hard pass
    assert check_criterion(pm_jay, {"age": 40, "ration_card": "bpl"})[0] == "soft"  # poor-household indicator only
    assert check_criterion(pm_jay, {"age": 40, "ration_card": "apl"})[0] == "fail"
    result, missing = check_criterion(pm_jay, {"age": 40})
    assert result == "unknown" and missing == ["ration_card"]                       # age already fails; only ask the other


def test_fully_specified_profile_gives_eligible():
    profile = {"age": 30, "has_bank_account": True}
    assert status("pmsby", profile) == "eligible"
    assert status("pmjjby", profile) == "eligible"


def test_any_failure_means_not_eligible():
    assert status("apy", {"age": 45, "has_bank_account": True, "pays_income_tax": False}) == "not_eligible"
    assert status("apy", {"age": 30, "has_bank_account": True, "pays_income_tax": True}) == "not_eligible"
    assert status("pm_kisan", {"owns_agri_land": False}) == "not_eligible"


def test_unknowns_make_it_likely_and_list_what_to_ask():
    ev = evaluate_scheme(scheme_by_id("pm_kisan"), {"owns_agri_land": True})
    assert ev["status"] == "likely"
    assert set(ev["missing_fields"]) == {"pays_income_tax", "govt_employee"}


def test_not_eligible_schemes_do_not_ask_questions():
    ev = evaluate_scheme(scheme_by_id("pm_kisan"), {"owns_agri_land": False})
    assert ev["missing_fields"] == []


def test_gruha_lakshmi_needs_karnataka_and_a_woman():
    base = {"gender": "female", "household_head": True, "pays_income_tax": False, "ration_card": "apl"}
    assert status("gruha_lakshmi", {**base, "state": "karnataka"}) == "eligible"
    assert status("gruha_lakshmi", {**base, "state": "other"}) == "not_eligible"
    assert status("gruha_lakshmi", {**base, "state": "karnataka", "gender": "male"}) == "not_eligible"


def test_pmay_is_never_a_hard_yes():
    # The income test is only an indicator (rural selection uses a government list).
    assert status("pmay", {"has_pucca_house": False, "annual_income": 100000}) == "likely"
    assert status("pmay", {"has_pucca_house": True}) == "not_eligible"


def test_sukanya_requires_a_young_daughter():
    assert status("ssy", {"girl_child_under_10": True}) == "eligible"
    assert status("ssy", {"girl_child_under_10": False}) == "not_eligible"


def test_results_are_ordered_eligible_first():
    order = {"eligible": 0, "likely": 1, "not_eligible": 2}
    ranks = [order[r["status"]] for r in evaluate_all({"age": 30, "has_bank_account": True})]
    assert ranks == sorted(ranks)


def test_next_questions_prioritises_fields_that_unblock_most_schemes():
    results = evaluate_all({"age": 30})
    questions = next_questions(results, limit=3)
    assert len(questions) == 3
    assert questions[0] in ("has_bank_account", "pays_income_tax", "govt_employee", "ration_card", "gender")


@pytest.mark.parametrize("scheme_id", [s for s in ["pm_kisan", "pm_jay", "apy", "pmjjby", "pmsby", "pmuy", "pmay", "ssy", "ignoaps", "mudra", "pm_vishwakarma", "gruha_lakshmi"]])
def test_empty_profile_is_never_not_eligible(scheme_id):
    """With no information we must never claim someone is ineligible."""
    assert status(scheme_id, {}) == "likely"
