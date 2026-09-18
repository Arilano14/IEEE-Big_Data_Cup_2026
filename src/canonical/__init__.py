"""AuditAI BI — Canonical Financial Data Model & Extraction Package."""

from src.canonical.parser import parse_questions, split_sections
from src.canonical.pipeline import process_case, run_canonical_pipeline
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

__all__ = [
    "AuditCase",
    "FilingEntity",
    "FilingDocument",
    "XbrlConcept",
    "XbrlContext",
    "XbrlUnit",
    "FinancialFact",
    "CalculationRelationship",
    "LabelRelationship",
    "LogicalProvenance",
    "split_sections",
    "parse_questions",
    "process_case",
    "run_canonical_pipeline",
]
