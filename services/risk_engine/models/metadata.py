"""Model metadata serialization and retrieval."""

import json
from pathlib import Path
from ..common.types import ModelMetadata
from ..common.exceptions import ModelCorruptError


class ModelMetadataManager:
    """Handles serialization and loading of ModelMetadata."""

    @staticmethod
    def save_metadata(metadata: ModelMetadata, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(), f, indent=2)
        return target_path

    @staticmethod
    def load_metadata(source_path: Path) -> ModelMetadata:
        if not source_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {source_path}")
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ModelMetadata(**data)
        except Exception as e:
            raise ModelCorruptError(f"Failed to parse metadata from {source_path}: {e}")
