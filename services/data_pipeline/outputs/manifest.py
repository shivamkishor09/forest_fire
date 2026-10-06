"""Pipeline run manifest generator recording reproducibility metadata and data provenance."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from ..common.types import DataManifest


class ManifestBuilder:
    """Builds and serializes reproducible DataManifest records."""

    @staticmethod
    def create_manifest(
        run_id: str,
        region_id: str,
        region_name: str,
        reference_date: str,
        grid_cells_count: int,
        feature_records_count: int,
        feature_columns: List[str],
        sources_ingested: Dict[str, Dict[str, Any]],
        output_files: Dict[str, str],
        target_column: Optional[str] = None,
        lookback_days: int = 7,
        resolution_meters: int = 500,
    ) -> DataManifest:
        now_iso = datetime.now(timezone.utc).isoformat()
        return DataManifest(
            run_id=run_id,
            created_at=now_iso,
            region_id=region_id,
            region_name=region_name,
            reference_date=reference_date,
            lookback_days=lookback_days,
            resolution_meters=resolution_meters,
            grid_cells_count=grid_cells_count,
            feature_records_count=feature_records_count,
            feature_columns=feature_columns,
            target_column=target_column,
            sources_ingested=sources_ingested,
            output_files=output_files,
            pipeline_version="phase-04-v1.0",
        )

    @staticmethod
    def save_manifest(manifest: DataManifest, target_file: Path) -> None:
        """Write manifest to JSON file."""
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2)
