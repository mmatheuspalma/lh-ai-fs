from evals.gold import GOLD, NEGATIVE_CONTROLS, gold_by_id


def test_gold_has_expected_ids():
    ids = {g.id for g in GOLD}
    assert {"privette_overstate", "seabright_misattributed", "date_contradiction",
            "ppe_contradiction"}.issubset(ids)


def test_privette_matcher_fires_on_citation_flag():
    g = gold_by_id("privette_overstate")
    flag = {"category": "citation", "case_name": "Privette v. Superior Court",
            "referent": "Privette v. Superior Court", "text": "overstates holding"}
    assert g.matches(flag)
    assert not g.matches({"category": "citation", "case_name": "Kellerman",
                          "referent": "Kellerman", "text": ""})


def test_date_matcher_fires_on_fact_flag():
    g = gold_by_id("date_contradiction")
    flag = {"category": "fact", "claim": "incident occurred March 14, 2021",
            "referent": "incident occurred March 14, 2021", "text": "record says March 12"}
    assert g.matches(flag)


def test_negative_control_sol_matcher():
    nc = next(n for n in NEGATIVE_CONTROLS if n.id == "sol_correct")
    flag = {"category": "citation", "case_name": "California Code of Civil Procedure Section 335.1",
            "referent": "...335.1", "text": "statute of limitations is two years"}
    assert nc.matches(flag)
