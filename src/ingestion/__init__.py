"""Ingestion package for acquiring and validating official challenge artifacts."""

from src.ingestion.config import IngestionConfig
from src.ingestion.downloader import ArtifactDownloader
from src.ingestion.extractor import DatasetExtractor
from src.ingestion.integrity_checker import IntegrityChecker
from src.ingestion.manifest import ManifestManager

__all__ = [
    "IngestionConfig",
    "ArtifactDownloader",
    "DatasetExtractor",
    "IntegrityChecker",
    "ManifestManager",
]
