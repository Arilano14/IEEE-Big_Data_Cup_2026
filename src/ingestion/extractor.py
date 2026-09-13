"""Extractor module executing organizer-specified transformation and strict data segregation."""

import hashlib
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyarrow.parquet as pq

from src.ingestion.config import IngestionConfig

logger = logging.getLogger(__name__)


def _maybe_json_decode(value: Any) -> str:
    """Decode string if double-encoded with JSON quotes, matching organizer specification."""
    if not isinstance(value, str):
        return str(value)
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        try:
            decoded = json.loads(text)
            if isinstance(decoded, str):
                return decoded
        except json.JSONDecodeError:
            return value
    return value


def _parse_answer(value: Any, row_index: int) -> Dict[str, str]:
    """Parse and validate FinMR answer dictionary."""
    if isinstance(value, dict):
        return {k: str(v) for k, v in value.items()}
    text = _maybe_json_decode(value)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return {k: str(v) for k, v in parsed.items()}
    except json.JSONDecodeError as exc:
        raise ValueError(f"Row {row_index}: Answer is not valid JSON: {text[:100]!r}") from exc
    raise ValueError(f"Row {row_index}: Answer must be a JSON object, got {type(parsed).__name__}")


class DatasetExtractor:
    """Unpacks raw FinMR parquet into physically segregated input and gold streams."""

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()

    def extract(self, parquet_path: Optional[Path] = None) -> Dict[str, Any]:
        """Read raw parquet, apply organizer normalization, and write segregated files."""
        source_path = parquet_path or self.config.RAW_PARQUET_PATH
        if not source_path.exists():
            raise FileNotFoundError(f"Parquet source not found at {source_path}")

        logger.info("Reading parquet table from %s", source_path)
        table = pq.read_table(source_path)
        pydict = table.to_pydict()

        num_rows = table.num_rows
        logger.info("Parquet table loaded with %d rows", num_rows)

        # Prepare destinations
        self.config.CHALLENGE_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
        self.config.EVALUATION_GOLD_DIR.mkdir(parents=True, exist_ok=True)

        input_records: List[Dict[str, Any]] = []
        gold_records: List[Dict[str, Any]] = []
        dqc_counter: Counter = Counter()

        for idx in range(num_rows):
            raw_id = pydict.get("id", [None])[idx]
            case_id = f"DEV_{raw_id:06d}" if isinstance(raw_id, int) else f"DEV_{idx:06d}"

            raw_dqc = pydict.get("dqc_id", [""])[idx]
            dqc_id = _maybe_json_decode(raw_dqc)
            dqc_counter[dqc_id] += 1

            raw_query = pydict.get("query", [""])[idx]
            query = _maybe_json_decode(raw_query)

            raw_answer = pydict.get("answer", [{}])[idx]
            answer = _parse_answer(raw_answer, idx)

            source_info = {
                "source_id": raw_id,
                "row_index": idx,
                "dataset": "TheFinAI/FinMR",
            }

            # Challenge input: strictly unlabeled query
            input_record = {
                "id": case_id,
                "dqc_id": dqc_id,
                "query": query,
            }
            input_records.append(input_record)

            # Evaluation gold: includes ground truth answer and lineage
            gold_record = {
                "id": case_id,
                "dqc_id": dqc_id,
                "query": query,
                "answer": answer,
                "source": source_info,
            }
            gold_records.append(gold_record)

        # Write unlabeled inputs
        logger.info("Writing %d challenge inputs to %s", len(input_records), self.config.CHALLENGE_INPUTS_FILE)
        with open(self.config.CHALLENGE_INPUTS_FILE, "w", encoding="utf-8") as f:
            for record in input_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Write gold answers
        logger.info("Writing %d gold cases to %s", len(gold_records), self.config.EVALUATION_GOLD_FILE)
        with open(self.config.EVALUATION_GOLD_FILE, "w", encoding="utf-8") as f:
            for record in gold_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Compute file checksums
        inputs_sha = self._compute_file_sha(self.config.CHALLENGE_INPUTS_FILE)
        gold_sha = self._compute_file_sha(self.config.EVALUATION_GOLD_FILE)

        # Write evaluation manifest
        manifest_data = {
            "dataset_name": "FinMR_Task3_PublicDev",
            "total_cases": num_rows,
            "dqc_distribution": dict(dqc_counter),
            "files": {
                "public_dev_inputs.jsonl": {
                    "path": str(self.config.CHALLENGE_INPUTS_FILE.relative_to(self.config.PROJECT_ROOT)),
                    "record_count": len(input_records),
                    "sha256": inputs_sha,
                },
                "public_dev_gold.jsonl": {
                    "path": str(self.config.EVALUATION_GOLD_FILE.relative_to(self.config.PROJECT_ROOT)),
                    "record_count": len(gold_records),
                    "sha256": gold_sha,
                },
            },
        }

        with open(self.config.EVALUATION_MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return {
            "total_records": num_rows,
            "dqc_counts": dict(dqc_counter),
            "inputs_file": self.config.CHALLENGE_INPUTS_FILE,
            "gold_file": self.config.EVALUATION_GOLD_FILE,
            "manifest_file": self.config.EVALUATION_MANIFEST_FILE,
        }

    @staticmethod
    def _compute_file_sha(path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
