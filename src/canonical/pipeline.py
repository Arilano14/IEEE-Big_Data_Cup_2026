"""AuditAI BI — Canonical Pipeline Runner.

Orchestrates the transformation of raw challenge inputs into relational Silver entities,
enforces semantic determinism, and writes authoritative Parquet datasets and inspection JSONL views.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pyarrow as pa
import pyarrow.parquet as pq

from src.canonical.parser import parse_questions, split_sections
from src.canonical.schemas import (
    AuditCase,
    CalculationRelationship,
    FilingDocument,
    FilingEntity,
    FinancialFact,
    LabelRelationship,
    XbrlConcept,
    XbrlContext,
    XbrlUnit,
)
from src.canonical.xbrl import (
    parse_calculation_linkbase,
    parse_instance_document,
    parse_label_linkbase,
    parse_schema_document,
    parse_taxonomy_document,
)


def process_case(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms a single Task 3 challenge input record into canonical entities.
    
    Args:
        rec: Dictionary from public_dev_inputs.jsonl with keys 'id', 'dqc_id', 'query'.
        
    Returns:
        Dictionary containing extracted entity instances.
    """
    case_id = rec["id"]
    dqc_id = rec["dqc_id"]
    raw_query = rec["query"]

    # 1. Split sections and extract question text
    sections, question_text = split_sections(raw_query)

    # 2. Parse target inquiries and period
    q_data = parse_questions(question_text)

    # 3. Parse Instance document
    instance_xml = sections.get("Instance document", "")
    contexts, units, facts, cik = parse_instance_document(
        instance_xml=instance_xml,
        case_id=case_id,
        full_query=raw_query,
    )

    # 4. Parse Schema document
    schema_xml = sections.get("Schema document", "")
    schema_concepts, target_ns, custom_pfx = parse_schema_document(schema_xml, case_id)

    # 5. Parse Linkbases
    calc_xml = sections.get("Calculation linkbase document", "")
    calc_rels = parse_calculation_linkbase(calc_xml, case_id, custom_prefix=custom_pfx or "us-gaap")

    label_xml = sections.get("Label linkbase document", "")
    label_rels = parse_label_linkbase(label_xml, case_id, custom_prefix=custom_pfx or "us-gaap")

    tax_xml = sections.get("US GAAP Taxonomy", "")
    tax_concepts = parse_taxonomy_document(tax_xml, case_id)

    # Combine concepts
    concepts = schema_concepts + tax_concepts

    # 6. Build AuditCase entity
    audit_case = AuditCase(
        case_id=case_id,
        dqc_id=dqc_id,
        target_concept=q_data["target_concept"],
        target_period_type=q_data["target_period_type"],
        target_start_date=q_data["target_start_date"],
        target_end_date=q_data["target_end_date"],
        target_instant_date=q_data["target_instant_date"],
        raw_question1=q_data["raw_question1"],
        raw_question2=q_data["raw_question2"],
        source_dataset="TheFinAI/FinMR",
    )

    # 7. Build FilingDocument entity
    filing_doc = FilingDocument(
        case_id=case_id,
        cik=cik or "UNKNOWN",
        target_namespace=target_ns,
        document_type="xbrl_filing_package",
    )

    # 8. Build FilingEntity if CIK found
    filing_entity = FilingEntity(cik=cik) if cik else None

    return {
        "case": audit_case,
        "filing_doc": filing_doc,
        "filing_entity": filing_entity,
        "contexts": contexts,
        "units": units,
        "facts": facts,
        "concepts": concepts,
        "calc_rels": calc_rels,
        "label_rels": label_rels,
    }


def compute_semantic_fingerprint(
    cases: List[Dict[str, Any]],
    facts: List[Dict[str, Any]],
    calc_rels: List[Dict[str, Any]],
) -> str:
    """Computes a deterministic SHA-256 fingerprint over normalized, sorted canonical records."""
    # 1. Sort cases by case_id
    sorted_cases = sorted(cases, key=lambda x: x["case_id"])

    # 2. Sort facts by composite key (case_id, concept_qname, context_id, unit_id, fact_id)
    sorted_facts = sorted(
        facts,
        key=lambda x: (
            x["case_id"],
            x["concept_qname"],
            x["context_id"],
            x["unit_id"] or "",
            x["fact_id"],
        ),
    )

    # 3. Sort calculation relationships by (case_id, role_uri, parent_concept, child_concept)
    sorted_calc = sorted(
        calc_rels,
        key=lambda x: (
            x["case_id"],
            x["role_uri"],
            x["parent_concept"],
            x["child_concept"],
        ),
    )

    payload = {
        "cases": sorted_cases,
        "facts": sorted_facts,
        "calc_rels": sorted_calc,
    }

    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def run_canonical_pipeline(
    input_path: str = "data/challenge/inputs/public_dev_inputs.jsonl",
    output_dir: str = "data/silver",
) -> Dict[str, Any]:
    """Executes the canonical transformation pipeline over all challenge input cases.
    
    Generates authoritative Parquet datasets and inspection JSONL files under output_dir.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    all_cases: List[Dict[str, Any]] = []
    all_filing_docs: List[Dict[str, Any]] = []
    entity_ciks: Set[str] = set()
    all_contexts: List[Dict[str, Any]] = []
    all_units: List[Dict[str, Any]] = []
    all_facts: List[Dict[str, Any]] = []
    concept_map: Dict[str, Dict[str, Any]] = {}  # qname -> concept dict
    all_calc_rels: List[Dict[str, Any]] = []
    all_label_rels: List[Dict[str, Any]] = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            res = process_case(rec)

            all_cases.append(res["case"].to_dict())
            all_filing_docs.append(res["filing_doc"].to_dict())
            if res["filing_entity"]:
                entity_ciks.add(res["filing_entity"].cik)

            for ctx in res["contexts"]:
                all_contexts.append(ctx.to_dict())

            for u in res["units"]:
                all_units.append(u.to_dict())

            for f_obj in res["facts"]:
                # Flatten fact with provenance for optimal columnar Parquet storage
                f_dict = f_obj.to_dict()
                prov = f_dict.pop("provenance", {}) or {}
                flat_f = {
                    **f_dict,
                    "provenance_dataset": prov.get("dataset"),
                    "provenance_artifact": prov.get("artifact"),
                    "provenance_section": prov.get("source_section"),
                    "provenance_document_type": prov.get("document_type"),
                    "provenance_filing_ref": prov.get("filing_reference"),
                    "provenance_element_locator": prov.get("element_locator"),
                    "provenance_char_offset_start": prov.get("char_offset_start"),
                    "provenance_char_offset_end": prov.get("char_offset_end"),
                }
                all_facts.append(flat_f)

            for c in res["concepts"]:
                c_dict = c.to_dict()
                concept_map[c.qname] = c_dict

            for rel in res["calc_rels"]:
                all_calc_rels.append(rel.to_dict())

            for l_rel in res["label_rels"]:
                all_label_rels.append(l_rel.to_dict())

    all_entities = [{"cik": cik, "entity_scheme": "http://www.sec.gov/CIK"} for cik in sorted(entity_ciks)]
    all_concepts = list(concept_map.values())

    # 1. Compute Semantic Fingerprint
    fingerprint = compute_semantic_fingerprint(all_cases, all_facts, all_calc_rels)

    # 2. Write Authoritative Parquet Tables
    datasets_to_write = {
        "audit_cases": all_cases,
        "filing_documents": all_filing_docs,
        "filing_entities": all_entities,
        "xbrl_contexts": all_contexts,
        "xbrl_units": all_units,
        "financial_facts": all_facts,
        "xbrl_concepts": all_concepts,
        "calculation_relationships": all_calc_rels,
        "label_relationships": all_label_rels,
    }

    record_counts = {}
    for name, data in datasets_to_write.items():
        pq_path = out_path / f"{name}.parquet"
        if data:
            tbl = pa.Table.from_pylist(data)
            pq.write_table(tbl, str(pq_path))
        else:
            # Write empty table with schema if empty
            tbl = pa.Table.from_pylist([{}])
            pq.write_table(tbl, str(pq_path))
        record_counts[name] = len(data)

    # 3. Write Optional Inspection JSONL Views
    for inspection_name in ["audit_cases", "financial_facts", "calculation_relationships"]:
        jsonl_path = out_path / f"{inspection_name}.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as jf:
            for row in datasets_to_write[inspection_name]:
                jf.write(json.dumps(row, ensure_ascii=False) + "\n")

    # 4. Write Provenance & Semantic Fingerprint Manifest
    manifest = {
        "source_input": input_path,
        "output_directory": str(out_path),
        "authoritative_format": "parquet",
        "inspection_format": "jsonl",
        "execution_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "semantic_fingerprint_sha256": fingerprint,
        "record_counts": record_counts,
    }

    manifest_path = out_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    return manifest


if __name__ == "__main__":
    result = run_canonical_pipeline()
    print("=" * 60)
    print("CANONICAL PIPELINE EXECUTION COMPLETED")
    print("=" * 60)
    print("Semantic Fingerprint:", result["semantic_fingerprint_sha256"])
    print("Record counts:")
    for k, v in result["record_counts"].items():
        print(f"  {k:30s}: {v}")
