"""Ingestion configuration specifying operational parameters and storage paths."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestionConfig:
    """Operational settings and directory paths for Phase 1 ingestion."""

    # Project filesystem anchors
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

    # Source endpoints
    SOURCE_REPO: str = "TheFinAI/FinMR"
    PARQUET_FILENAME: str = "test-00000-of-00001.parquet"
    SOURCE_URL: str = (
        "https://huggingface.co/datasets/TheFinAI/FinMR/resolve/main/data/test-00000-of-00001.parquet"
    )

    # Physical storage locations (Input vs. Gold Separation)
    RAW_BRONZE_DIR: Path = PROJECT_ROOT / "data" / "bronze" / "finmr"
    CHALLENGE_INPUTS_DIR: Path = PROJECT_ROOT / "data" / "challenge" / "inputs"
    EVALUATION_GOLD_DIR: Path = PROJECT_ROOT / "data" / "evaluation" / "gold"

    # Specific file targets
    RAW_PARQUET_PATH: Path = RAW_BRONZE_DIR / "test-00000-of-00001.parquet"
    BRONZE_MANIFEST_PATH: Path = RAW_BRONZE_DIR / "manifest.json"

    CHALLENGE_INPUTS_FILE: Path = CHALLENGE_INPUTS_DIR / "public_dev_inputs.jsonl"
    EVALUATION_GOLD_FILE: Path = EVALUATION_GOLD_DIR / "public_dev_gold.jsonl"
    EVALUATION_MANIFEST_FILE: Path = EVALUATION_GOLD_DIR / "public_dev_manifest.json"

    # Operational network parameters
    TIMEOUT_SECONDS: float = 60.0
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0
    CHUNK_SIZE_BYTES: int = 65536  # 64 KB streaming chunks
