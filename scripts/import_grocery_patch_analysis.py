"""Import durable grocery patch-analysis outputs for the public report.

The analytical definitions and classifications remain owned by the sibling
``delivery-analytics`` repository. This script performs presentation-only
aggregation and records the source contract in the generated JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


RETAILER_ORDER = ["coop", "sainsburys", "morrisons"]
PATCH_TYPE_ORDER = ["Fill-in", "Edge expansion", "Independent island"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_export(analytics_root: Path) -> dict[str, object]:
    patch_size_path = (
        analytics_root
        / "data"
        / "processed"
        / "grocery_delivery"
        / "justeat_only_patch_size.csv"
    )
    size_summary_path = (
        analytics_root
        / "outputs"
        / "tables"
        / "06_patch_size_summary_by_retailer.csv"
    )
    composition_path = (
        analytics_root
        / "outputs"
        / "tables"
        / "06_boundary_length_50pct_composition.csv"
    )
    density_path = (
        analytics_root
        / "outputs"
        / "tables"
        / "06_patch_size_lsoa_density_by_retailer.csv"
    )

    patch_rows = read_rows(patch_size_path)
    summary_rows = read_rows(size_summary_path)
    composition_rows = read_rows(composition_path)
    density_rows = read_rows(density_path)

    summary_by_retailer = {row["retailer"]: row for row in summary_rows}
    composition_by_retailer: dict[str, dict[str, dict[str, str]]] = {}
    for row in composition_rows:
        composition_by_retailer.setdefault(row["retailer"], {})[
            row["patch_type"]
        ] = row

    retailers = []
    for retailer in RETAILER_ORDER:
        retailer_patches = [row for row in patch_rows if row["retailer"] == retailer]
        retailer_density = [
            row for row in density_rows if row["retailer"] == retailer
        ]
        total = len(retailer_patches)
        summary = summary_by_retailer[retailer]
        composition = composition_by_retailer[retailer]

        if total != int(float(summary["patches"])):
            raise ValueError(f"Patch count does not reconcile for {retailer}")
        if set(composition) != set(PATCH_TYPE_ORDER):
            raise ValueError(f"Morphology classes are incomplete for {retailer}")

        retailers.append(
            {
                "retailer": retailer,
                "label": summary["retailer_label"],
                "patches": total,
                "medianLsoas": int(float(summary["median_LSOAs"])),
                "p75Lsoas": int(float(summary["p75_LSOAs"])),
                "maxLsoas": int(float(summary["max_LSOAs"])),
                "medianPopulation": int(float(summary["median_population"])),
                "atMostTenPct": round(
                    sum(
                        1
                        for row in retailer_patches
                        if int(row["n_lsoa"]) <= 10
                    )
                    / total
                    * 100,
                    2,
                ),
                "density": [
                    {
                        "x": round(float(row["x_value"]), 6),
                        "logX": round(float(row["log10_x_value"]), 6),
                        "y": round(float(row["smoothed_density"]), 8),
                    }
                    for row in retailer_density
                    if float(row["x_value"]) >= 1
                ],
                "morphology": [
                    {
                        "sourceLabel": patch_type,
                        "label": (
                            "Edge-adjacent complement"
                            if patch_type == "Edge expansion"
                            else patch_type
                        ),
                        "patches": int(composition[patch_type]["patches"]),
                        "patchSharePct": round(
                            float(composition[patch_type]["patch_share_pct"]), 2
                        ),
                        "lsoas": int(
                            composition[patch_type]["Just_Eat_only_LSOAs"]
                        ),
                        "lsoaSharePct": round(
                            float(composition[patch_type]["LSOA_share_pct"]), 2
                        ),
                    }
                    for patch_type in PATCH_TYPE_ORDER
                ],
            }
        )

    return {
        "schemaVersion": 1,
        "sourceContract": {
            "repository": "delivery-analytics",
            "notebook": "06_grocery_delivery_patch_topology.ipynb",
            "files": [
                patch_size_path.relative_to(analytics_root).as_posix(),
                size_summary_path.relative_to(analytics_root).as_posix(),
                composition_path.relative_to(analytics_root).as_posix(),
                density_path.relative_to(analytics_root).as_posix(),
            ],
            "geography": "England LSOA 2021",
            "patchDefinition": (
                "Maximal Rook-connected component of Just Eat-only LSOAs; "
                "shared boundary must exceed one metre."
            ),
            "primaryMorphologyRule": (
                "50% boundary-length enclosure ratio; unknown-direct boundary excluded."
            ),
        },
        "retailers": retailers,
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
        default=(
            showcase_root
            / "src"
            / "data"
            / "generated"
            / "grocery_patch_analysis.json"
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    payload = build_export(arguments.analytics_root.resolve())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {arguments.output}")
