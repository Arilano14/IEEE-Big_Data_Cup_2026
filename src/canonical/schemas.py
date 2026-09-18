"""AuditAI BI — Canonical Financial Data Model & Data Contract.

Defines immutable, strongly-typed data contracts for all Silver-tier canonical entities
using Python standard library dataclasses.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LogicalProvenance:
    """Unbroken logical source lineage tracking for financial facts."""
    dataset: str
    artifact: str
    case_id: str
    source_section: str
    document_type: str
    xbrl_concept: str
    context_id: str
    element_locator: int
    filing_reference: Optional[str] = None
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditCase:
    """Represents an individual Task 3 competition case and inquiry boundary."""
    case_id: str
    dqc_id: str
    target_concept: str
    target_period_type: str  # "duration" | "instant"
    raw_question1: str
    raw_question2: str
    target_start_date: Optional[str] = None
    target_end_date: Optional[str] = None
    target_instant_date: Optional[str] = None
    source_dataset: str = "TheFinAI/FinMR"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FilingEntity:
    """SEC registrant entity dimension keyed by 10-digit CIK."""
    cik: str
    entity_scheme: str = "http://www.sec.gov/CIK"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FilingDocument:
    """Filing package metadata scoping custom namespaces and document types."""
    case_id: str
    cik: str
    target_namespace: Optional[str] = None
    document_type: str = "xbrl_filing_package"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XbrlConcept:
    """XBRL concept definition from schema documents and US-GAAP taxonomy."""
    concept_id: str
    qname: str
    prefix: str
    local_name: str
    namespace_uri: Optional[str] = None
    data_type: Optional[str] = None
    period_type: Optional[str] = None
    balance_type: Optional[str] = None
    substitution_group: Optional[str] = None
    is_abstract: bool = False
    is_nillable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XbrlContext:
    """Temporal and dimensional scope for reported facts in instance documents."""
    context_key: str
    case_id: str
    context_id: str
    cik: str
    period_type: str  # "duration" | "instant"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instant_date: Optional[str] = None
    dimensions_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XbrlUnit:
    """Unit of measure for reported values."""
    unit_key: str
    case_id: str
    unit_id: str
    measure: str
    unit_type: str  # "currency" | "shares" | "rate" | "other"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinancialFact:
    """Atomic reported numerical financial facts extracted verbatim from instance."""
    fact_id: str
    case_id: str
    concept_qname: str
    context_id: str
    unit_id: Optional[str] = None
    raw_value: Optional[str] = None
    numeric_value: Optional[float] = None
    decimals: Optional[str] = None
    scale: Optional[int] = None
    sign: str = "N/A"  # "+" | "-" | "0" | "N/A"
    is_nil: bool = False
    provenance: Optional[LogicalProvenance] = None

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.provenance is not None:
            res["provenance"] = self.provenance.to_dict()
        return res


@dataclass(frozen=True)
class CalculationRelationship:
    """Directed summation relationships from calculation linkbases."""
    relationship_id: str
    case_id: str
    role_uri: str
    parent_concept: str
    child_concept: str
    weight: float
    order: Optional[float] = None
    arcrole: str = "http://www.xbrl.org/2003/arcrole/summation-item"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabelRelationship:
    """Human-readable concept labels from label linkbases."""
    label_id: str
    case_id: str
    concept_qname: str
    role_uri: str
    label_text: str
    language: str = "en-US"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
