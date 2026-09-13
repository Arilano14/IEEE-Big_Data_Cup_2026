"""Unit tests for ArtifactDownloader."""

from pathlib import Path
import pytest

from src.ingestion.config import IngestionConfig
from src.ingestion.downloader import ArtifactDownloader


def test_downloader_init_custom_config(tmp_path: Path):
    custom_config = IngestionConfig(
        RAW_BRONZE_DIR=tmp_path / "bronze",
        RAW_PARQUET_PATH=tmp_path / "bronze" / "test.parquet",
    )
    downloader = ArtifactDownloader(config=custom_config)
    assert downloader.config.RAW_PARQUET_PATH == tmp_path / "bronze" / "test.parquet"


def test_downloader_invalid_url_fails(tmp_path: Path):
    custom_config = IngestionConfig(
        SOURCE_URL="https://invalid-non-existent-domain-xyz123.com/file.parquet",
        RAW_BRONZE_DIR=tmp_path / "bronze",
        RAW_PARQUET_PATH=tmp_path / "bronze" / "test.parquet",
        MAX_RETRIES=1,
        TIMEOUT_SECONDS=2.0,
    )
    downloader = ArtifactDownloader(config=custom_config)
    with pytest.raises(RuntimeError) as exc_info:
        downloader.download()
    assert "Failed to download" in str(exc_info.value)
