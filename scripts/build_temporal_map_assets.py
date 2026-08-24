"""Export Dash scheduled opening-time caches as compact browser assets."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
HOURS = list(range(24))
EXPECTED_AREAS = 43_064
EXPECTED_PARENTS = 350


def compact_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def write_gzip_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as destination:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=destination,
            compresslevel=9,
            mtime=0,
        ) as compressed:
            compressed.write(compact_json(payload))


def quantile_breaks(values: list[np.ndarray]) -> list[float]:
    combined = np.concatenate(values)
    return [
        round(float(value), 1)
        for value in np.quantile(combined, [0.05, 0.25, 0.5, 0.75, 0.95])
    ]


def build_temporal_assets(dashboard_root: Path, output_root: Path) -> dict:
    area_root = dashboard_root / "data" / "cache" / "opening_by_hour"
    parent_root = dashboard_root / "data" / "cache" / "parent_opening_by_hour"
    if not area_root.exists() or not parent_root.exists():
        raise FileNotFoundError("Dash scheduled opening-time caches were not found")

    area_ids: list[str] | None = None
    parent_ids: list[str] | None = None
    area_distributions: list[np.ndarray] = []
    parent_distributions: list[np.ndarray] = []
    run_ids: set[str] = set()
    files: dict[str, str] = {}

    for day in DAYS:
        for hour in HOURS:
            stem = f"{day}_{hour:02d}"
            area = pd.read_parquet(
                area_root / f"{stem}.parquet",
                columns=["area_id", "open_restaurant_count", "opening_run_id"],
            ).sort_values("area_id")
            parent = pd.read_parquet(
                parent_root / f"{stem}.parquet",
                columns=["parent_id", "median_open_restaurant_count", "opening_run_id"],
            ).sort_values("parent_id")

            current_area_ids = area["area_id"].astype(str).tolist()
            current_parent_ids = parent["parent_id"].astype(str).tolist()
            if len(current_area_ids) != EXPECTED_AREAS or len(set(current_area_ids)) != EXPECTED_AREAS:
                raise ValueError(f"Unexpected area keys in {stem}")
            if len(current_parent_ids) != EXPECTED_PARENTS or len(set(current_parent_ids)) != EXPECTED_PARENTS:
                raise ValueError(f"Unexpected parent keys in {stem}")
            if area_ids is None:
                area_ids = current_area_ids
                parent_ids = current_parent_ids
            elif current_area_ids != area_ids or current_parent_ids != parent_ids:
                raise ValueError(f"Geography order differs in {stem}")

            area_values = pd.to_numeric(
                area["open_restaurant_count"], errors="raise"
            ).fillna(0).round().astype("int32").to_numpy()
            parent_values = pd.to_numeric(
                parent["median_open_restaurant_count"], errors="raise"
            ).fillna(0).round(1).astype("float32").to_numpy()
            if (area_values < 0).any() or (parent_values < 0).any():
                raise ValueError(f"Negative scheduled opening count in {stem}")

            filename = f"{day.lower()}_{hour:02d}.json.gz"
            write_gzip_json(
                output_root / filename,
                {
                    "p": parent_values.tolist(),
                    "a": area_values.tolist(),
                },
            )
            files[f"{day}:{hour}"] = filename
            area_distributions.append(area_values)
            parent_distributions.append(parent_values)
            run_ids.update(area["opening_run_id"].dropna().astype(str).unique())
            run_ids.update(parent["opening_run_id"].dropna().astype(str).unique())

    manifest = {
        "metric": "open_restaurant_count",
        "label": "Scheduled open restaurants",
        "parent_label": "Median open per small area",
        "semantics": "Derived from delivery opening intervals; not observed open-now availability.",
        "days": DAYS,
        "hours": HOURS,
        "default_day": "Friday",
        "default_hour": 20,
        "area_ids": area_ids,
        "parent_ids": parent_ids,
        "files": files,
        "breaks": quantile_breaks(parent_distributions),
        "child_breaks": quantile_breaks(area_distributions),
        "opening_run_ids": sorted(run_ids),
    }
    write_gzip_json(output_root / "manifest.json.gz", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    showcase_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dashboard-root",
        type=Path,
        default=showcase_root.parent / "delivery-map-dashboard",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=showcase_root / "public" / "map" / "v1" / "temporal",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_temporal_assets(args.dashboard_root, args.output_root)
    print(
        f"Built {len(manifest['files'])} scheduled opening-time assets for "
        f"{len(manifest['area_ids']):,} areas and {len(manifest['parent_ids'])} LADs"
    )


if __name__ == "__main__":
    main()
