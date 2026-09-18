"""Tests for XBRL XML parsing of facts, contexts, units, and relationships."""
from src.canonical.xbrl import (
    parse_calculation_linkbase,
    parse_instance_document,
    parse_label_linkbase,
    parse_schema_document,
    parse_taxonomy_document,
)


def test_parse_instance_sample():
    sample_instance = """<?xml version='1.0' encoding='UTF-8'?>
    <xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2021-01-31" xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
        <context id="ctx_dur">
            <entity><identifier scheme="http://www.sec.gov/CIK">0000004904</identifier></entity>
            <period><startDate>2021-01-01</startDate><endDate>2021-12-31</endDate></period>
        </context>
        <unit id="usd"><measure>iso4217:USD</measure></unit>
        <us-gaap:Assets contextRef="ctx_dur" unitRef="usd" decimals="-3">123,456,000</us-gaap:Assets>
        <us-gaap:NetIncomeLoss contextRef="ctx_dur" unitRef="usd" decimals="-3">(5,000)</us-gaap:NetIncomeLoss>
    </xbrl>
    """
    contexts, units, facts, cik = parse_instance_document(sample_instance, "DEV_TEST")
    assert cik == "0000004904"
    assert len(contexts) == 1
    assert contexts[0].period_type == "duration"
    assert len(units) == 1
    assert units[0].unit_type == "currency"
    assert len(facts) == 2

    # Verify fact 1: positive with commas
    f1 = facts[0]
    assert f1.concept_qname == "us-gaap:Assets"
    assert f1.raw_value == "123,456,000"
    assert f1.numeric_value == 123456000.0
    assert f1.sign == "+"
    assert f1.decimals == "-3"

    # Verify fact 2: negative with parentheses
    f2 = facts[1]
    assert f2.concept_qname == "us-gaap:NetIncomeLoss"
    assert f2.raw_value == "(5,000)"
    assert f2.numeric_value == -5000.0
    assert f2.sign == "-"


def test_parse_calculation_sample():
    sample_calc = """<?xml version='1.0' encoding='UTF-8'?>
    <linkbase xmlns="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
        <calculationLink xlink:type="extended" xlink:role="http://example.com/role/BalanceSheet">
            <loc xlink:type="locator" xlink:href="schema.xsd#us-gaap_Assets" xlink:label="loc_assets"/>
            <loc xlink:type="locator" xlink:href="schema.xsd#us-gaap_AssetsCurrent" xlink:label="loc_assets_curr"/>
            <calculationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/summation-item"
                            xlink:from="loc_assets" xlink:to="loc_assets_curr" weight="1.0" order="1.0"/>
        </calculationLink>
    </linkbase>
    """
    rels = parse_calculation_linkbase(sample_calc, "DEV_TEST")
    assert len(rels) == 1
    r = rels[0]
    assert r.parent_concept == "us-gaap:Assets"
    assert r.child_concept == "us-gaap:AssetsCurrent"
    assert r.weight == 1.0
    assert r.order == 1.0


def test_parse_taxonomy_text_block():
    sample_tax = """
    [Concept Core]
    ID: us-gaap:CashAndCashEquivalentsAtCarryingValue
    Label: Cash and Cash Equivalents, at Carrying Value
    Type: xbrli:monetaryItemType | Balance: debit | PeriodType: instant | Abstract: False
    """
    concepts = parse_taxonomy_document(sample_tax, "DEV_TEST")
    assert len(concepts) == 1
    c = concepts[0]
    assert c.qname == "us-gaap:CashAndCashEquivalentsAtCarryingValue"
    assert c.data_type == "xbrli:monetaryItemType"
    assert c.balance_type == "debit"
    assert c.period_type == "instant"
    assert c.is_abstract is False
