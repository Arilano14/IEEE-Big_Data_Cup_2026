"""Provenance manifest management and cryptographic hash generation."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ArtifactManifest:
    """Immutable data record capturing artifact provenance and cryptographic digest."""

    artifact_name: str
    source_repository: str
    source_url: str
    retrieval_timestamp_utc: str
    file_size_bytes: int
    sha256_checksum: str
    declared_record_count: int
    license: str = "CC-BY-4.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ManifestManager:
    """Manages creation, serialization, and deserialization of artifact manifests."""

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA-256 hexadecimal digest for a target file in streaming chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def generate_manifest(
        cls,
        file_path: Path,
        source_url: str,
        source_repo: str,
        declared_record_count: int,
    ) -> ArtifactManifest:
        """Generate manifest from a local physical artifact file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact not found at {file_path}")

        file_size = file_path.stat().st_size
        sha256_hash = cls.compute_sha256(file_path)
        timestamp = datetime.now(timezone.utc).isoformat()

        return ArtifactManifest(
            artifact_name=file_path.name,
            source_repository=source_repo,
            source_url=source_url,
            retrieval_timestamp_utc=timestamp,
            file_size_bytes=file_size,
            sha256_checksum=sha256_hash,
            declared_record_count=declared_record_count,
        )

    @staticmethod
    def save_manifest(manifest: ArtifactManifest, destination_path: Path) -> None:
        """Write manifest as formatted JSON."""
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with open(destination_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)

    @staticmethod
    def load_manifest(manifest_path: Path) -> ArtifactManifest:
        """Load manifest from a JSON file."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found at {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ArtifactManifest(**data)
