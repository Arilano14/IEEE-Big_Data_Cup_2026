"""Tests for markdown section splitting and question parsing."""
import json
from src.canonical.parser import parse_questions, split_sections


def test_split_sections_structure():
    sample_query = (
        "## Schema document\n<schema></schema>\n"
        "## Presentation linkbase document\n<linkbase></linkbase>\n"
        "## Calculation linkbase document\n<calc></calc>\n"
        "## Definition linkbase document\n<def></def>\n"
        "## Label linkbase document\n<label></label>\n"
        "## Instance document\n<xbrl></xbrl>\n"
        "## US GAAP Taxonomy\n[Concept Core]\nID: us-gaap:Assets\n"
        "Question1: What's the reported value of us-gaap:Assets in the Instance document for the period 2021-01-01 to 2021-12-31?\n"
        "Question2: What's the actual value of us-gaap:Assets in the Instance document for the period 2021-01-01 to 2021-12-31, calculated based on the calculation relationship?\nAnswer:"
    )
    sections, q_text = split_sections(sample_query)
    assert "Schema document" in sections
    assert "Instance document" in sections
    assert "US GAAP Taxonomy" in sections
    assert "Question1:" in q_text
    assert "Question2:" in q_text


def test_parse_questions_duration():
    q_text = (
        "Question1: What's the reported value of us-gaap:PaymentsToAcquirePropertyPlantAndEquipment in the Instance document for the period 2021-09-01 to 2021-11-30?\n"
        "Question2: What's the actual value of us-gaap:PaymentsToAcquirePropertyPlantAndEquipment in the Instance document for the period 2021-09-01 to 2021-11-30, calculated based on the calculation relationship?\nAnswer:"
    )
    res = parse_questions(q_text)
    assert res["target_concept"] == "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
    assert res["target_period_type"] == "duration"
    assert res["target_start_date"] == "2021-09-01"
    assert res["target_end_date"] == "2021-11-30"
    assert res["target_instant_date"] is None


def test_parse_questions_instant():
    q_text = (
        "Question1: What's the reported value of us-gaap:DerivativeAverageForwardPrice in the Instance document for the period 2021-12-31?\n"
        "Question2: What's the actual value of us-gaap:DerivativeAverageForwardPrice in the Instance document for the period 2021-12-31, calculated based on the calculation relationship?\nAnswer:"
    )
    res = parse_questions(q_text)
    assert res["target_concept"] == "us-gaap:DerivativeAverageForwardPrice"
    assert res["target_period_type"] == "instant"
    assert res["target_instant_date"] == "2021-12-31"
    assert res["target_start_date"] is None
    assert res["target_end_date"] is None


def test_all_332_cases_question_parsing():
    """Verify that 100% of live challenge inputs parse non-empty concepts and valid period types."""
    with open("data/challenge/inputs/public_dev_inputs.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            _, q_text = split_sections(rec["query"])
            res = parse_questions(q_text)
            assert res["target_concept"] != "", f"Failed concept extraction on {rec['id']}"
            assert res["target_period_type"] in ["duration", "instant"], f"Invalid period type on {rec['id']}"
            if res["target_period_type"] == "duration":
                assert res["target_start_date"] is not None
                assert res["target_end_date"] is not None
            else:
                assert res["target_instant_date"] is not None
