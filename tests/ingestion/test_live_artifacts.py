"""Integration assertions verifying actual downloaded live Phase 1 artifacts."""

import json
from src.ingestion.config import IngestionConfig
from src.ingestion.integrity_checker import IntegrityChecker
from src.ingestion.manifest import ManifestManager


def test_live_bronze_parquet_and_manifest():
    config = IngestionConfig()
    assert config.RAW_PARQUET_PATH.exists()
    assert config.BRONZE_MANIFEST_PATH.exists()

    manifest = ManifestManager.load_manifest(config.BRONZE_MANIFEST_PATH)
    assert manifest.file_size_bytes == 4787195
    assert manifest.sha256_checksum == "a47cbef89ffd9e52b1b41340d9605314b36a46805cba7c1718e780399bdb50df"
    assert manifest.declared_record_count == 332


def test_live_challenge_inputs_integrity_and_zero_leakage():
    config = IngestionConfig()
    checker = IntegrityChecker(config=config)

    result = checker.check_inputs_leakage_and_integrity(expected_count=332)
    assert result["passed"] is True
    assert result["records_checked"] == 332
    assert result["leakage_violations"] == 0
    assert result["malformed_lines"] == 0


def test_live_evaluation_gold_integrity():
    config = IngestionConfig()
    checker = IntegrityChecker(config=config)

    result = checker.check_gold_integrity(expected_count=332)
    assert result["passed"] is True
    assert result["records_checked"] == 332
    assert result["missing_answer_keys"] == 0
    assert result["malformed_lines"] == 0


def test_live_dqc_rule_distribution():
    config = IngestionConfig()
    assert config.EVALUATION_MANIFEST_FILE.exists()

    with open(config.EVALUATION_MANIFEST_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["total_cases"] == 332
    dist = meta["dqc_distribution"]
    assert dist["DQC_US_0117"] == 120
    assert dist["DQC_US_0015"] == 110
    assert dist["DQC_US_0126"] == 102
