"""Serializes and renders data quality audit reports into JSON and Markdown."""

import json
from pathlib import Path
from ..common.types import QualityReport


class QualityReportWriter:
    """Writes QualityReport into JSON and human-readable Markdown format."""

    @staticmethod
    def save_json(report: QualityReport, target_file: Path) -> None:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

    @staticmethod
    def save_markdown(report: QualityReport, target_file: Path) -> None:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        md_lines = [
            f"# Data Pipeline Quality Report: {report.run_id}",
            f"",
            f"- **Execution Timestamp:** {report.created_at}",
            f"- **Total Feature Records:** {report.total_records}",
            f"- **Clean Records:** {report.clean_records_pct}%",
            f"- **Imputed Records:** {report.imputed_records_pct}%",
            f"",
            f"## Feature Completeness",
            f"",
            f"| Feature Name | Completeness (%) | Status |",
            f"|---|---|---|",
        ]

        for feat, comp in report.feature_completeness_pct.items():
            status = "PASS" if comp >= 95.0 else ("WARN" if comp >= 80.0 else "POOR")
            md_lines.append(f"| `{feat}` | {comp:.1f}% | {status} |")

        md_lines.extend([
            f"",
            f"## Summary Statistics",
            f"",
            f"| Feature | Min | Max | Mean | StdDev |",
            f"|---|---|---|---|---|",
        ])

        for feat, stats in report.summary_statistics.items():
            md_lines.append(
                f"| `{feat}` | {stats.get('min', 0):.2f} | {stats.get('max', 0):.2f} | "
                f"{stats.get('mean', 0):.2f} | {stats.get('std', 0):.2f} |"
            )

        if report.warnings:
            md_lines.extend([
                f"",
                f"## Quality Warnings",
                f"",
            ])
            for w in report.warnings:
                md_lines.append(f"- [!] {w}")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")
