"""Unit tests for DatasetExtractor and transformation helpers."""

import json
from pathlib import Path
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from src.ingestion.config import IngestionConfig
from src.ingestion.extractor import DatasetExtractor, _maybe_json_decode, _parse_answer


def test_maybe_json_decode_strings():
    assert _maybe_json_decode('"DQC_US_0015"') == "DQC_US_0015"
    assert _maybe_json_decode("DQC_US_0015") == "DQC_US_0015"
    assert _maybe_json_decode(123) == "123"
    assert _maybe_json_decode('{"a": 1}') == '{"a": 1}'  # not a quoted string literal


def test_parse_answer():
    valid_dict = {"extracted_value": "100", "calculated_value": "-100"}
    assert _parse_answer(valid_dict, 0) == valid_dict

    valid_json_str = '{"extracted_value": "500", "calculated_value": "500"}'
    assert _parse_answer(valid_json_str, 1) == {"extracted_value": "500", "calculated_value": "500"}

    with pytest.raises(ValueError) as exc:
        _parse_answer("invalid-json", 2)
    assert "Answer is not valid JSON" in str(exc.value)


def test_dataset_extractor_synthetic_parquet(tmp_path: Path):
    parquet_path = tmp_path / "mock.parquet"
    inputs_file = tmp_path / "inputs.jsonl"
    gold_file = tmp_path / "gold.jsonl"
    manifest_file = tmp_path / "manifest.json"

    # Create mock parquet table with FinMR schema
    data = {
        "id": [0, 1],
        "dqc_id": ['"DQC_US_0015"', '"DQC_US_0117"'],
        "query": ['"Test Query 1"', '"Test Query 2"'],
        "answer": [
            '{"extracted_value": "-100", "calculated_value": "100"}',
            '{"extracted_value": "200", "calculated_value": "200"}',
        ],
    }
    table = pa.Table.from_pydict(data)
    pq.write_table(table, parquet_path)

    config = IngestionConfig(
        PROJECT_ROOT=tmp_path,
        RAW_PARQUET_PATH=parquet_path,
        CHALLENGE_INPUTS_DIR=tmp_path / "inputs",
        EVALUATION_GOLD_DIR=tmp_path / "gold",
        CHALLENGE_INPUTS_FILE=inputs_file,
        EVALUATION_GOLD_FILE=gold_file,
        EVALUATION_MANIFEST_FILE=manifest_file,
    )

    extractor = DatasetExtractor(config=config)
    summary = extractor.extract(parquet_path=parquet_path)

    assert summary["total_records"] == 2
    assert summary["dqc_counts"]["DQC_US_0015"] == 1
    assert summary["dqc_counts"]["DQC_US_0117"] == 1

    # Verify inputs file contains NO answer keys
    with open(inputs_file, "r", encoding="utf-8") as f:
        inputs_rows = [json.loads(line) for line in f]
    assert len(inputs_rows) == 2
    assert inputs_rows[0]["id"] == "DEV_000000"
    assert inputs_rows[0]["dqc_id"] == "DQC_US_0015"
    assert inputs_rows[0]["query"] == "Test Query 1"
    assert "answer" not in inputs_rows[0]

    # Verify gold file contains answers
    with open(gold_file, "r", encoding="utf-8") as f:
        gold_rows = [json.loads(line) for line in f]
    assert len(gold_rows) == 2
    assert gold_rows[0]["answer"]["extracted_value"] == "-100"
