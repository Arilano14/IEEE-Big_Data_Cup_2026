"""Resilient artifact streaming downloader with retry and backoff."""

import logging
import time
from pathlib import Path
from typing import Optional

import httpx

from src.ingestion.config import IngestionConfig

logger = logging.getLogger(__name__)


class ArtifactDownloader:
    """Streams remote artifacts to local disk with exponential backoff."""

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()

    def download(self, url: Optional[str] = None, destination: Optional[Path] = None) -> Path:
        """Download artifact via streaming HTTP with retry logic and atomic rename."""
        target_url = url or self.config.SOURCE_URL
        target_path = destination or self.config.RAW_PARQUET_PATH

        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_suffix(".tmp")

        retries = 0
        backoff = self.config.BACKOFF_FACTOR

        while retries < self.config.MAX_RETRIES:
            try:
                logger.info("Initiating download from %s -> %s (attempt %d/%d)",
                            target_url, target_path, retries + 1, self.config.MAX_RETRIES)

                with httpx.Client(timeout=self.config.TIMEOUT_SECONDS, follow_redirects=True) as client:
                    with client.stream("GET", target_url) as response:
                        response.raise_for_status()

                        with open(temp_path, "wb") as f:
                            for chunk in response.iter_bytes(chunk_size=self.config.CHUNK_SIZE_BYTES):
                                f.write(chunk)

                # Atomic replace on successful complete stream
                temp_path.replace(target_path)
                logger.info("Successfully downloaded artifact (%d bytes) to %s",
                            target_path.stat().st_size, target_path)
                return target_path

            except (httpx.HTTPError, OSError) as exc:
                retries += 1
                logger.warning("Download failed on attempt %d: %s", retries, exc)
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)

                if retries >= self.config.MAX_RETRIES:
                    raise RuntimeError(
                        f"Failed to download {target_url} after {self.config.MAX_RETRIES} attempts: {exc}"
                    ) from exc

                sleep_time = backoff ** retries
                logger.info("Sleeping %.1f seconds before retry...", sleep_time)
                time.sleep(sleep_time)

        raise RuntimeError(f"Unexpected termination while downloading {target_url}")
