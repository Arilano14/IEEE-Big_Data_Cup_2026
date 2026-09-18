"""Tests for the end-to-end canonical pipeline execution and Parquet generation."""
from pathlib import Path
import pyarrow.parquet as pq

from src.canonical.pipeline import run_canonical_pipeline


def test_pipeline_execution_and_file_existence(tmp_path):
    output_dir = tmp_path / "silver_test"
    manifest = run_canonical_pipeline(
        input_path="data/challenge/inputs/public_dev_inputs.jsonl",
        output_dir=str(output_dir),
    )

    # 1. Verify manifest attributes
    assert manifest["record_counts"]["audit_cases"] == 332
    assert manifest["record_counts"]["financial_facts"] > 0
    assert manifest["semantic_fingerprint_sha256"] != ""

    # 2. Verify all Parquet files exist
    expected_tables = [
        "audit_cases",
        "filing_documents",
        "filing_entities",
        "xbrl_contexts",
        "xbrl_units",
        "financial_facts",
        "xbrl_concepts",
        "calculation_relationships",
        "label_relationships",
    ]
    for table_name in expected_tables:
        p = output_dir / f"{table_name}.parquet"
        assert p.exists(), f"Missing parquet file {p}"
        tbl = pq.read_table(str(p))
        assert len(tbl) == manifest["record_counts"][table_name]

    # 3. Verify inspection JSONL views
    for inspection_name in ["audit_cases", "financial_facts", "calculation_relationships"]:
        jp = output_dir / f"{inspection_name}.jsonl"
        assert jp.exists(), f"Missing jsonl inspection file {jp}"
