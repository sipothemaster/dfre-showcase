"""Build privacy-safe static GeoJSON assets for the MapLibre explorer.

The first public map release keeps the dashboard's proven two-level loading
pattern: one simplified LAD overview and one small-area file fetched only when
a LAD is selected. Unlike Dash, all interaction happens in the browser and no
Python callback or cloud service is required at runtime.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


EXPECTED_AREAS = 43_064
CATEGORY_CODES = {
    "Both channels": 0,
    "Direct only": 1,
    "Just Eat only": 2,
    "Neither observed": 3,
    "Direct unresolved": 4,
}
CHANNEL_COLUMNS = {
    "coop": "co",
    "morrisons_fast": "mo",
    "sainsburys_fast": "sa",
    "iceland": "ic",
}


def number(value, digits: int = 2):
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def integer(value):
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


def quantile_breaks(values: pd.Series, digits: int = 2) -> list[float]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    quantiles = clean.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).tolist()
    return [round(float(value), digits) for value in quantiles]


def build_assets(
    dashboard_root: Path,
    channel_csv: Path,
    output_root: Path,
) -> dict:
    area = pd.read_parquet(dashboard_root / "data/cache/area_delivery_coverage.parquet")
    lookup = pd.read_parquet(dashboard_root / "data/cache/area_parent_lookup.parquet")
    parent = pd.read_parquet(dashboard_root / "data/cache/parent_delivery_coverage.parquet")
    channels = pd.read_csv(channel_csv, dtype=str)

    for frame, key, label, expected in [
        (area, "area_id", "area coverage", EXPECTED_AREAS),
        (lookup, "area_id", "parent lookup", EXPECTED_AREAS),
        (parent, "parent_id", "parent coverage", 350),
    ]:
        if len(frame) != expected or frame[key].nunique() != expected:
            raise ValueError(f"Unexpected {label} keys: {len(frame):,} rows")

    expected_channel_rows = EXPECTED_AREAS * len(CHANNEL_COLUMNS)
    if len(channels) != expected_channel_rows:
        raise ValueError(
            f"Expected {expected_channel_rows:,} channel rows, found {len(channels):,}"
        )
    channels["channel_code"] = channels["channel_category"].map(CATEGORY_CODES)
    if channels["channel_code"].isna().any():
        raise ValueError("Unrecognised channel category")

    channel_wide = channels.pivot(
        index="geography_code", columns="comparison", values="channel_code"
    ).rename(columns=CHANNEL_COLUMNS)
    metrics = area.merge(lookup, on="area_id", how="inner", validate="one_to_one")
    metrics = metrics.merge(
        channel_wide,
        left_on="area_id",
        right_index=True,
        how="inner",
        validate="one_to_one",
    )
    if len(metrics) != EXPECTED_AREAS:
        raise ValueError("Area metrics and channel geography sets do not match")
    area_by_id = metrics.set_index("area_id").to_dict("index")

    parent_channel = channels.merge(
        lookup,
        left_on="geography_code",
        right_on="area_id",
        how="inner",
        validate="many_to_one",
    )
    parent_channel["is_justeat_only"] = (
        parent_channel["channel_category"] == "Just Eat only"
    ).astype(float)
    platform_rates = (
        parent_channel.groupby(["parent_id", "comparison"], observed=True)[
            "is_justeat_only"
        ]
        .mean()
        .mul(100)
        .unstack("comparison")
        .rename(columns=CHANNEL_COLUMNS)
    )
    platform_rates = platform_rates.add_suffix("_je")
    parent = parent.merge(
        platform_rates,
        left_on="parent_id",
        right_index=True,
        how="left",
        validate="one_to_one",
    )
    parent_by_id = parent.set_index("parent_id").to_dict("index")

    parent_source = load_json(
        dashboard_root / "data/boundaries/uk_lad_2024_bgc_simplified.geojson"
    )
    parent_features = []
    for feature in parent_source.get("features", []):
        old = feature.get("properties") or {}
        parent_id = str(old.get("parent_id") or old.get("LAD24CD") or "")
        row = parent_by_id.get(parent_id)
        if not row:
            continue
        feature["properties"] = {
            "id": parent_id,
            "name": str(row["parent_name"]),
            "n": integer(row["child_area_count"]),
            "pop": integer(row["population_total"]),
            "r": number(row["median_deliverable_restaurant_count"], 1),
            "ff": number(row["median_fast_food_restaurant_count"], 1),
            "ffd": number(row["fast_food_restaurant_density_per_100k"], 1),
            "ffs": number(row["fast_food_restaurant_share"], 4),
            "g": number(row["median_grocery_restaurant_count"], 1),
            **{
                column: number(row.get(column), 2)
                for column in ["co_je", "mo_je", "sa_je", "ic_je"]
            },
        }
        parent_features.append(feature)
    if len(parent_features) != 350:
        raise ValueError(f"Expected 350 coverage LAD features, found {len(parent_features)}")
    write_json(
        output_root / "parents.geojson",
        {"type": "FeatureCollection", "features": parent_features},
    )

    children_output = output_root / "children"
    children_output.mkdir(parents=True, exist_ok=True)
    child_source = dashboard_root / "data/boundaries/children_by_parent"
    child_count = 0
    child_bytes = 0
    for parent_id in sorted(parent_by_id):
        source_path = child_source / f"{parent_id}.geojson"
        payload = load_json(source_path)
        features = []
        for feature in payload.get("features", []):
            old = feature.get("properties") or {}
            area_id = str(old.get("area_id") or old.get("LSOA21CD") or old.get("DZCode") or "")
            row = area_by_id.get(area_id)
            if not row:
                continue
            feature["properties"] = {
                "id": area_id,
                "name": str(row["area_name"]),
                "parent": parent_id,
                "type": "DZ" if str(row["area_type"]).lower().startswith("data") else "LSOA",
                "pop": integer(row["population_total"]),
                "r": integer(row["deliverable_restaurant_count"]),
                "ff": integer(row["fast_food_restaurant_count"]),
                "ffd": number(row["fast_food_restaurant_density_per_100k"], 1),
                "ffs": number(row["fast_food_restaurant_share"], 4),
                "g": integer(row["grocery_restaurant_count"]),
                **{column: integer(row[column]) for column in CHANNEL_COLUMNS.values()},
            }
            features.append(feature)
        destination = children_output / f"{parent_id}.geojson"
        write_json(destination, {"type": "FeatureCollection", "features": features})
        child_count += len(features)
        child_bytes += destination.stat().st_size
    if child_count != EXPECTED_AREAS:
        raise ValueError(f"Expected {EXPECTED_AREAS:,} child features, wrote {child_count:,}")

    manifest = {
        "release": "v1",
        "parents": len(parent_features),
        "children": child_count,
        "child_files": len(parent_by_id),
        "child_bytes": child_bytes,
        "geography_design": "One representative postcode per LSOA/Data Zone",
        "metrics": {
            "r": {
                "label": "Deliverable restaurants",
                "parent_label": "Median per small area",
                "breaks": quantile_breaks(parent["median_deliverable_restaurant_count"], 1),
                "child_breaks": quantile_breaks(area["deliverable_restaurant_count"], 1),
            },
            "ff": {
                "label": "Fast-food restaurants",
                "parent_label": "Median per small area",
                "breaks": quantile_breaks(parent["median_fast_food_restaurant_count"], 1),
                "child_breaks": quantile_breaks(area["fast_food_restaurant_count"], 1),
            },
            "ffs": {
                "label": "Fast-food share",
                "parent_label": "Pooled share",
                "breaks": quantile_breaks(parent["fast_food_restaurant_share"], 4),
                "child_breaks": quantile_breaks(area["fast_food_restaurant_share"], 4),
            },
            "g": {
                "label": "Grocery listings",
                "parent_label": "Median per small area",
                "breaks": quantile_breaks(parent["median_grocery_restaurant_count"], 1),
                "child_breaks": quantile_breaks(area["grocery_restaurant_count"], 1),
            },
        },
        "channel_codes": {str(code): label for label, code in CATEGORY_CODES.items()},
    }
    write_json(output_root / "manifest.json", manifest)
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
        "--channel-csv",
        type=Path,
        default=showcase_root / "public/data/v1/retailer_channel_areas.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=showcase_root / "public/map/v1",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_assets(args.dashboard_root, args.channel_csv, args.output_root)
    print(
        f"Built {manifest['parents']} LADs and {manifest['children']:,} child areas "
        f"across {manifest['child_files']} static files"
    )


if __name__ == "__main__":
    main()
