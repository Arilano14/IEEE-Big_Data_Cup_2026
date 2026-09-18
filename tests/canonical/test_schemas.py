"""Tests for canonical dataclass schemas, immutability, and serialization."""
import pytest
from dataclasses import FrozenInstanceError

from src.canonical.schemas import (
    AuditCase,
    CalculationRelationship,
    FilingDocument,
    FilingEntity,
    FinancialFact,
    LabelRelationship,
    LogicalProvenance,
    XbrlConcept,
    XbrlContext,
    XbrlUnit,
)


def test_audit_case_immutability():
    case = AuditCase(
        case_id="DEV_000000",
        dqc_id="DQC_US_0015",
        target_concept="us-gaap:Assets",
        target_period_type="duration",
        raw_question1="Q1",
        raw_question2="Q2",
    )
    with pytest.raises(FrozenInstanceError):
        case.case_id = "DEV_999999"  # type: ignore


def test_financial_fact_provenance_serialization():
    prov = LogicalProvenance(
        dataset="TheFinAI/FinMR",
        artifact="test-00000-of-00001.parquet",
        case_id="DEV_000001",
        source_section="## Instance document",
        document_type="xbrl_instance",
        xbrl_concept="us-gaap:Cash",
        context_id="FD2021Q4",
        element_locator=1,
        filing_reference="0000004904",
        char_offset_start=10,
        char_offset_end=20,
    )
    fact = FinancialFact(
        fact_id="fact-uuid-1",
        case_id="DEV_000001",
        concept_qname="us-gaap:Cash",
        context_id="FD2021Q4",
        unit_id="usd",
        raw_value="1,284",
        numeric_value=1284.0,
        decimals="-3",
        scale=None,
        sign="+",
        is_nil=False,
        provenance=prov,
    )
    d = fact.to_dict()
    assert d["fact_id"] == "fact-uuid-1"
    assert d["numeric_value"] == 1284.0
    assert d["provenance"]["dataset"] == "TheFinAI/FinMR"
    assert d["provenance"]["element_locator"] == 1


def test_calculation_relationship_contract():
    rel = CalculationRelationship(
        relationship_id="rel-uuid-1",
        case_id="DEV_000001",
        role_uri="http://example.com/role",
        parent_concept="us-gaap:Assets",
        child_concept="us-gaap:AssetsCurrent",
        weight=1.0,
        order=1.0,
    )
    d = rel.to_dict()
    assert d["weight"] == 1.0
    assert d["arcrole"] == "http://www.xbrl.org/2003/arcrole/summation-item"
