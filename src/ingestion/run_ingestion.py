"""Execution script for Phase 1 ingestion pipeline."""

import json
import logging
import sys
from pathlib import Path

import pyarrow.parquet as pq

from src.ingestion.config import IngestionConfig
from src.ingestion.downloader import ArtifactDownloader
from src.ingestion.extractor import DatasetExtractor
from src.ingestion.integrity_checker import IntegrityChecker
from src.ingestion.manifest import ManifestManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_ingestion")


def main() -> int:
    config = IngestionConfig()
    logger.info("Starting Phase 1 Ingestion Pipeline...")
    logger.info("Project Root: %s", config.PROJECT_ROOT)

    # 1. Download official public development artifact
    downloader = ArtifactDownloader(config=config)
    parquet_path = downloader.download()

    # 2. Inspect declared metadata and record count
    table = pq.read_table(parquet_path)
    declared_count = table.num_rows
    logger.info("Parquet artifact verified with %d declared rows", declared_count)

    # 3. Generate and persist cryptographic provenance manifest
    manifest = ManifestManager.generate_manifest(
        file_path=parquet_path,
        source_url=config.SOURCE_URL,
        source_repo=config.SOURCE_REPO,
        declared_record_count=declared_count,
    )
    ManifestManager.save_manifest(manifest, config.BRONZE_MANIFEST_PATH)
    logger.info("Saved provenance manifest to %s (SHA-256: %s)",
                config.BRONZE_MANIFEST_PATH, manifest.sha256_checksum)

    # 4. Extract into segregated challenge inputs and evaluation gold streams
    extractor = DatasetExtractor(config=config)
    extraction_summary = extractor.extract(parquet_path=parquet_path)
    logger.info("Extracted %d total records. DQC distribution: %s",
                extraction_summary["total_records"], extraction_summary["dqc_counts"])

    # 5. Run full integrity, manifest reconciliation, and leakage checks
    checker = IntegrityChecker(config=config)
    report = checker.run_all_checks()

    logger.info("Integrity Verification Summary:\n%s", json.dumps(report, indent=2))

    if not report["overall_passed"]:
        logger.error("Phase 1 Ingestion Verification FAILED!")
        return 1

    logger.info("Phase 1 Ingestion Pipeline COMPLETED SUCCESSFULLY with 100% verification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
