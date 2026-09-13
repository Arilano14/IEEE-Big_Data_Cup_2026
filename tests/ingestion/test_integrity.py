"""Unit tests for ManifestManager and IntegrityChecker."""

import json
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.ingestion.config import IngestionConfig
from src.ingestion.integrity_checker import IntegrityChecker
from src.ingestion.manifest import ArtifactManifest, ManifestManager


def test_manifest_manager_sha256_and_serialization(tmp_path: Path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("AuditAI BI Sample File", encoding="utf-8")

    sha256 = ManifestManager.compute_sha256(sample_file)
    assert len(sha256) == 64

    manifest = ManifestManager.generate_manifest(
        file_path=sample_file,
        source_url="https://example.com/sample.txt",
        source_repo="test/repo",
        declared_record_count=1,
    )

    manifest_file = tmp_path / "manifest.json"
    ManifestManager.save_manifest(manifest, manifest_file)
    loaded = ManifestManager.load_manifest(manifest_file)

    assert loaded.artifact_name == "sample.txt"
    assert loaded.sha256_checksum == sha256
    assert loaded.declared_record_count == 1


def test_integrity_checker_detects_leakage(tmp_path: Path):
    leaky_inputs = tmp_path / "leaky_inputs.jsonl"
    # Row 1 is clean, Row 2 contains leaked gold answer
    with open(leaky_inputs, "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "DEV_000000", "dqc_id": "DQC_US_0015", "query": "Clean"}) + "\n")
        f.write(json.dumps({"id": "DEV_000001", "dqc_id": "DQC_US_0015", "query": "Leaked", "answer": {"extracted_value": "100"}}) + "\n")

    checker = IntegrityChecker()
    result = checker.check_inputs_leakage_and_integrity(inputs_path=leaky_inputs, expected_count=2)

    assert result["passed"] is False
    assert result["leakage_violations"] == 1
    assert "answer" in result["leakage_details"][0]["forbidden_keys"]


def test_integrity_checker_clean_verification(tmp_path: Path):
    clean_inputs = tmp_path / "clean_inputs.jsonl"
    clean_gold = tmp_path / "clean_gold.jsonl"
    parquet_file = tmp_path / "test.parquet"
    manifest_file = tmp_path / "manifest.json"

    # Mock parquet
    table = pa.Table.from_pydict({"id": [0], "val": ["x"]})
    pq.write_table(table, parquet_file)

    # Manifest
    manifest = ManifestManager.generate_manifest(
        file_path=parquet_file,
        source_url="https://example.com/test.parquet",
        source_repo="test/repo",
        declared_record_count=1,
    )
    ManifestManager.save_manifest(manifest, manifest_file)

    # Inputs
    clean_inputs.write_text(json.dumps({"id": "DEV_000000", "dqc_id": "DQC_1", "query": "Q"}) + "\n", encoding="utf-8")

    # Gold
    clean_gold.write_text(json.dumps({
        "id": "DEV_000000",
        "dqc_id": "DQC_1",
        "query": "Q",
        "answer": {"extracted_value": "10", "calculated_value": "10"}
    }) + "\n", encoding="utf-8")

    config = IngestionConfig(
        PROJECT_ROOT=tmp_path,
        RAW_PARQUET_PATH=parquet_file,
        BRONZE_MANIFEST_PATH=manifest_file,
        CHALLENGE_INPUTS_FILE=clean_inputs,
        EVALUATION_GOLD_FILE=clean_gold,
    )

    checker = IntegrityChecker(config=config)
    report = checker.run_all_checks()

    assert report["overall_passed"] is True
    assert report["inputs_verification"]["leakage_violations"] == 0
    assert report["gold_verification"]["missing_answer_keys"] == 0
