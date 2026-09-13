"""Cryptographic integrity and data leakage verification module."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pyarrow.parquet as pq

from src.ingestion.config import IngestionConfig
from src.ingestion.manifest import ManifestManager

logger = logging.getLogger(__name__)


class IntegrityChecker:
    """Performs cryptographic verification, row count auditing, and data leakage checks."""

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()

    def check_bronze_artifact(
        self,
        parquet_path: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Verify that downloaded raw parquet matches manifest size, checksum, and row count."""
        target_parquet = parquet_path or self.config.RAW_PARQUET_PATH
        target_manifest = manifest_path or self.config.BRONZE_MANIFEST_PATH

        if not target_parquet.exists():
            return {"passed": False, "error": f"Parquet file missing: {target_parquet}"}
        if not target_manifest.exists():
            return {"passed": False, "error": f"Manifest file missing: {target_manifest}"}

        manifest = ManifestManager.load_manifest(target_manifest)

        actual_size = target_parquet.stat().st_size
        actual_sha = ManifestManager.compute_sha256(target_parquet)

        table = pq.read_table(target_parquet)
        actual_rows = table.num_rows

        size_match = actual_size == manifest.file_size_bytes
        sha_match = actual_sha == manifest.sha256_checksum
        rows_match = actual_rows == manifest.declared_record_count

        passed = size_match and sha_match and rows_match

        return {
            "passed": passed,
            "actual_size_bytes": actual_size,
            "manifest_size_bytes": manifest.file_size_bytes,
            "actual_sha256": actual_sha,
            "manifest_sha256": manifest.sha256_checksum,
            "actual_record_count": actual_rows,
            "manifest_record_count": manifest.declared_record_count,
            "matches": {
                "size": size_match,
                "sha256": sha_match,
                "record_count": rows_match,
            },
        }

    def check_inputs_leakage_and_integrity(
        self,
        inputs_path: Optional[Path] = None,
        expected_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Verify inputs file integrity and assert ZERO gold answer leakage."""
        target_inputs = inputs_path or self.config.CHALLENGE_INPUTS_FILE
        if not target_inputs.exists():
            return {"passed": False, "error": f"Inputs file missing: {target_inputs}"}

        records_checked = 0
        forbidden_keys_detected = []
        malformed_lines = 0

        # Hard boundary: these keys must NEVER exist in the inputs stream
        forbidden_keys = {"answer", "gold_extracted", "gold_calculated", "extracted_value", "calculated_value"}

        with open(target_inputs, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                try:
                    record = json.loads(line)
                    records_checked += 1

                    # Check for leakage
                    present_forbidden = forbidden_keys.intersection(record.keys())
                    if present_forbidden:
                        forbidden_keys_detected.append({
                            "line": line_no,
                            "id": record.get("id"),
                            "forbidden_keys": list(present_forbidden),
                        })

                except json.JSONDecodeError:
                    malformed_lines += 1

        count_passed = True
        if expected_count is not None:
            count_passed = records_checked == expected_count

        no_leakage = len(forbidden_keys_detected) == 0
        no_malformed = malformed_lines == 0

        passed = count_passed and no_leakage and no_malformed

        return {
            "passed": passed,
            "records_checked": records_checked,
            "expected_count": expected_count,
            "count_matched": count_passed,
            "malformed_lines": malformed_lines,
            "leakage_violations": len(forbidden_keys_detected),
            "leakage_details": forbidden_keys_detected[:5],  # Sample first 5 if any
        }

    def check_gold_integrity(
        self,
        gold_path: Optional[Path] = None,
        expected_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Verify gold evaluation file integrity and required answer keys."""
        target_gold = gold_path or self.config.EVALUATION_GOLD_FILE
        if not target_gold.exists():
            return {"passed": False, "error": f"Gold file missing: {target_gold}"}

        records_checked = 0
        missing_answer_keys = 0
        malformed_lines = 0

        with open(target_gold, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    records_checked += 1

                    answer = record.get("answer", {})
                    if "extracted_value" not in answer or "calculated_value" not in answer:
                        missing_answer_keys += 1

                except json.JSONDecodeError:
                    malformed_lines += 1

        count_passed = True
        if expected_count is not None:
            count_passed = records_checked == expected_count

        passed = count_passed and missing_answer_keys == 0 and malformed_lines == 0

        return {
            "passed": passed,
            "records_checked": records_checked,
            "expected_count": expected_count,
            "count_matched": count_passed,
            "missing_answer_keys": missing_answer_keys,
            "malformed_lines": malformed_lines,
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run complete integrity, provenance, and leakage verification suite."""
        bronze_result = self.check_bronze_artifact()
        expected_rows = bronze_result.get("actual_record_count")

        inputs_result = self.check_inputs_leakage_and_integrity(expected_count=expected_rows)
        gold_result = self.check_gold_integrity(expected_count=expected_rows)

        overall_passed = (
            bronze_result.get("passed", False)
            and inputs_result.get("passed", False)
            and gold_result.get("passed", False)
        )

        return {
            "overall_passed": overall_passed,
            "bronze_verification": bronze_result,
            "inputs_verification": inputs_result,
            "gold_verification": gold_result,
        }
