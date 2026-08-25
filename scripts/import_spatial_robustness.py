"""Import the validated notebook-04 spatial robustness outputs.

The showcase owns presentation only. Statistical estimates remain owned by
``delivery-analytics``; this import records the exact source files and hashes
used to build the static public component.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def as_float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def build_export(analytics_root: Path) -> dict[str, object]:
    table_root = analytics_root / "outputs" / "tables"
    paths = {
        "predictions": table_root / "04_sem_imd_predictions.csv",
        "model_summary": table_root / "04_sem_model_summary.csv",
        "contrasts": table_root / "04_sem_imd_endpoint_contrasts.csv",
        "rook_audit": table_root / "04_lsoa_rook_weights_audit.csv",
        "jaccard_summary": table_root / "04_jaccard_sem_model_summary.csv",
        "jaccard_contrasts": table_root
        / "04_jaccard_sem_imd_endpoint_contrasts.csv",
        "mixed_contrasts": table_root
        / "04_mixed_sem_imd_endpoint_contrasts.csv",
    }
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(path)

    prediction_rows = [
        row
        for row in read_rows(paths["predictions"])
        if row["specification"] == "Fast-food share"
        and row["estimator"] in {"OLS HC3", "SEM GMM"}
    ]
    curves = []
    for estimator in ("OLS HC3", "SEM GMM"):
        values = [
            {
                "imd_decile": int(float(row["imd_decile"])),
                "imd_score": round(as_float(row, "imd_score"), 6),
                "prediction_pct": round(
                    as_float(row, "predicted_original_scale"), 6
                ),
                "ci_lower_pct": round(
                    as_float(row, "ci_lower_original_scale"), 6
                ),
                "ci_upper_pct": round(
                    as_float(row, "ci_upper_original_scale"), 6
                ),
            }
            for row in prediction_rows
            if row["estimator"] == estimator
        ]
        values.sort(key=lambda row: row["imd_decile"])
        if [row["imd_decile"] for row in values] != list(range(1, 11)):
            raise ValueError(
                f"Expected one prediction for every IMD decile for {estimator}"
            )
        curves.append({"estimator": estimator, "values": values})

    model_rows = read_rows(paths["model_summary"])
    share_model = next(
        row for row in model_rows if row["specification"] == "Fast-food share"
    )
    contrast_rows = [
        row
        for row in read_rows(paths["contrasts"])
        if row["specification"] == "Fast-food share"
    ]
    ols_contrast = next(row for row in contrast_rows if row["estimator"] == "OLS HC3")
    sem_contrast = next(row for row in contrast_rows if row["estimator"] == "SEM GMM")
    rook_audit = next(
        row
        for row in read_rows(paths["rook_audit"])
        if row["analysis_sample"] == "Positive-denominator share sample"
    )

    jaccard_rows = read_rows(paths["jaccard_summary"])
    jaccard_contrasts = [
        row
        for row in read_rows(paths["jaccard_contrasts"])
        if row["model"].startswith("Jaccard SEM")
    ]
    mixed_contrasts = read_rows(paths["mixed_contrasts"])

    return {
        "title": "Spatial robustness of the deprivation gradient",
        "claim_status": "exploratory robustness analysis",
        "provenance": {
            "repository": "delivery-analytics",
            "notebook": "notebooks/04_robustness_extensions.ipynb",
            "sources": [
                source_record(path, analytics_root) for path in paths.values()
            ],
        },
        "sample": {
            "geography": "England LSOA 2021",
            "n": int(share_model["n"]),
            "missing_data_rule": share_model["missing_data_rule"],
        },
        "outcome": "Empirical-logit fast-food share, displayed as a percentage",
        "imd_display": (
            "Continuous-score models evaluated at the median IMD score within "
            "each official decile; contrast is decile 1 minus decile 10"
        ),
        "formula": share_model["formula"],
        "baseline": {
            "estimator": "OLS with HC3 covariance",
            "residual_morans_i": round(
                as_float(share_model, "ols_residual_morans_i"), 3
            ),
            "imd_change_percentage_points": round(
                as_float(ols_contrast, "absolute_change"), 2
            ),
        },
        "rook_sem": {
            "estimator": share_model["estimator"],
            "weights": "Rook contiguity with shared boundary > 1 metre; row-standardised",
            "undirected_edges": int(rook_audit["undirected_rook_pairs"]),
            "lambda": round(as_float(share_model, "lambda"), 3),
            "filtered_residual_morans_i": round(
                as_float(share_model, "sem_filtered_morans_i"), 3
            ),
            "imd_change_percentage_points": round(
                as_float(sem_contrast, "absolute_change"), 2
            ),
        },
        "network_sensitivity": {
            "definition": (
                "Jaccard similarity between the sets of deliverable food "
                "restaurants at each LSOA representative postcode"
            ),
            "top_k": [int(row["k"]) for row in jaccard_rows],
            "lambda_range": [
                round(min(as_float(row, "lambda") for row in jaccard_rows), 3),
                round(max(as_float(row, "lambda") for row in jaccard_rows), 3),
            ],
            "imd_change_range_percentage_points": [
                round(
                    min(
                        as_float(row, "change_percentage_points")
                        for row in jaccard_contrasts
                    ),
                    2,
                ),
                round(
                    max(
                        as_float(row, "change_percentage_points")
                        for row in jaccard_contrasts
                    ),
                    2,
                ),
            ],
            "all_mixed_weight_contrast_intervals_include_zero": all(
                as_float(row, "change_ci_lower") <= 0
                <= as_float(row, "change_ci_upper")
                for row in mixed_contrasts
            ),
            "interpretation": (
                "Alternative network and mixed weights also flatten the IMD "
                "gradient, but near-boundary lambdas, shifting prediction "
                "levels and remaining residual dependence indicate model "
                "instability rather than a preferred spatial specification."
            ),
        },
        "curves": curves,
    }


def parse_args() -> argparse.Namespace:
    showcase_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analytics-root",
        type=Path,
        default=showcase_root.parent / "delivery-analytics",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=showcase_root
        / "src"
        / "data"
        / "generated"
        / "spatial_robustness.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_export(args.analytics_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
