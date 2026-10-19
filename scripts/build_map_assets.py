"""Build privacy-safe static GeoJSON assets for the MapLibre explorer.

The first public map release keeps the dashboard's proven two-level loading
pattern: one simplified LAD overview and one small-area file fetched only when
a LAD is selected. Unlike Dash, all interaction happens in the browser and no
Python callback or cloud service is required at runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


EXPECTED_AREAS = 43_064
RAPID_SERVICE_COUNT = 3


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


def sha256_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_rapid_grocery_coverage(package_root: Path) -> tuple[pd.DataFrame, dict]:
    """Build an anonymous 0-3 rapid-grocery coverage count.

    The source package owns each service's FastDelivery definition. This
    presentation import counts affirmative observations and retains Unknown as
    a separate count so it is never silently treated as No.
    """

    source_paths = []
    for path in sorted((package_root / "retailers").glob("*.csv")):
        columns = pd.read_csv(path, nrows=0).columns
        if "FastDelivery" in columns:
            source_paths.append(path)
    if len(source_paths) != RAPID_SERVICE_COUNT:
        raise ValueError(
            f"Expected {RAPID_SERVICE_COUNT} rapid-grocery inputs with a FastDelivery field, "
            f"found {len(source_paths)}"
        )
    frames: list[pd.DataFrame] = []
    expected_geographies: set[str] | None = None

    for index, path in enumerate(source_paths, start=1):
        frame = pd.read_csv(
            path,
            dtype=str,
            usecols=["GeographyCode", "FastDelivery"],
        )
        if len(frame) != EXPECTED_AREAS or frame["GeographyCode"].nunique() != EXPECTED_AREAS:
            raise ValueError(
                f"Unexpected rapid-grocery geography keys in input {index}: "
                f"{len(frame):,} rows"
            )
        statuses = set(frame["FastDelivery"].dropna().unique())
        if not statuses.issubset({"Yes", "No", "Unknown"}):
            raise ValueError(
                f"Unexpected FastDelivery values in input {index}: {sorted(statuses)}"
            )
        geography_set = set(frame["GeographyCode"])
        if expected_geographies is None:
            expected_geographies = geography_set
        elif geography_set != expected_geographies:
            raise ValueError("Rapid-grocery input geography sets do not match")
        frames.append(
            frame.set_index("GeographyCode")["FastDelivery"].rename(f"service_{index}")
        )

    statuses = pd.concat(frames, axis=1)
    coverage = pd.DataFrame(index=statuses.index)
    coverage["fc"] = statuses.eq("Yes").sum(axis=1).astype(int)
    coverage["fu"] = statuses.eq("Unknown").sum(axis=1).astype(int)

    if not coverage["fc"].between(0, len(source_paths)).all():
        raise ValueError("Rapid-grocery coverage count fell outside 0-3")

    readme_path = package_root / "README.md"
    contract = {
        "source_owner": "WebscrapingDeliveryAvailability",
        "package": package_root.name,
        "services": len(source_paths),
        "rows_per_service": EXPECTED_AREAS,
        "geography": "One repaired representative postcode per LSOA 2021 or Data Zone 2022",
        "coverage_definition": "Count of services with FastDelivery=Yes",
        "unresolved_definition": "Count of services with FastDelivery=Unknown; Unknown is not treated as No",
        "combined_input_sha256": sha256_files(source_paths),
        "readme_sha256": sha256_files([readme_path]),
    }
    return coverage, contract


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
    grocery_package: Path,
    output_root: Path,
    cache_directory: Path | None = None,
) -> dict:
    cache = cache_directory or dashboard_root / "data/cache/nutrition_society_v2"
    area = pd.read_parquet(cache / "area_delivery_coverage.parquet")
    lookup = pd.read_parquet(cache / "area_parent_lookup.parquet")
    parent = pd.read_parquet(cache / "parent_delivery_coverage.parquet")
    contract = load_json(cache / "source_contract.json")
    rapid_coverage, rapid_contract = load_rapid_grocery_coverage(grocery_package)

    for frame, key, label, expected in [
        (area, "area_id", "area coverage", EXPECTED_AREAS),
        (lookup, "area_id", "parent lookup", EXPECTED_AREAS),
        (parent, "parent_id", "parent coverage", 350),
    ]:
        if len(frame) != expected or frame[key].nunique() != expected:
            raise ValueError(f"Unexpected {label} keys: {len(frame):,} rows")

    metrics = area.merge(lookup, on="area_id", how="inner", validate="one_to_one")
    metrics = metrics.merge(
        rapid_coverage,
        left_on="area_id",
        right_index=True,
        how="inner",
        validate="one_to_one",
    )
    if len(metrics) != EXPECTED_AREAS:
        raise ValueError("Area metrics and rapid-grocery geography sets do not match")
    area_by_id = metrics.set_index("area_id").to_dict("index")

    parent_rapid = metrics.groupby("parent_id", observed=True).agg(
        fc=("fc", "mean"),
        fu=("fu", "sum"),
    )
    parent = parent.merge(
        parent_rapid,
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
            "r": number(row["median_food_restaurant_count"], 1),
            "ff": number(row["median_fast_food_restaurant_count"], 1),
            "ffs": number(row["fast_food_restaurant_share"], 4),
            "g": number(row["median_grocery_restaurant_count"], 1),
            "fc": number(row["fc"], 2),
            "fu": integer(row["fu"]),
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
                "r": integer(row["food_restaurant_count"]),
                "ff": integer(row["fast_food_restaurant_count"]),
                "ffs": number(row["fast_food_restaurant_share"], 4),
                "g": integer(row["grocery_restaurant_count"]),
                "schedule_known": integer(row["known_schedule_count"]),
                "schedule_unknown": integer(row["unknown_schedule_count"]),
                "fc": integer(row["fc"]),
                "fu": integer(row["fu"]),
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
        "taxonomy_version": contract["taxonomy"]["version"],
        "source_contract": contract,
        "rapid_grocery_contract": rapid_contract,
        "restaurant_denominator": "Distinct deliverable non-retail restaurant IDs",
        "metrics": {
            "r": {
                "label": "Total deliverable restaurants",
                "parent_label": "Median per small area",
                "breaks": quantile_breaks(parent["median_food_restaurant_count"], 1),
                "child_breaks": quantile_breaks(area["food_restaurant_count"], 1),
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
            "fc": {
                "label": "Rapid grocery availability",
                "parent_label": "Mean observed services per small area",
                "breaks": [0, 1, 2, 3],
                "child_breaks": [0, 1, 2, 3],
                "semantics": "Count of three services observed as available; unresolved observations remain separate",
            },
        },
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
        "--grocery-package",
        type=Path,
        default=(
            showcase_root.parent
            / "WebscrapingDeliveryAvailability"
            / "data/output/grocery-delivery-data-package-2026-10-19"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=showcase_root / "public/map/v1",
    )
    parser.add_argument("--cache-directory", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_assets(
        args.dashboard_root,
        args.grocery_package,
        args.output_root,
        args.cache_directory,
    )
    print(
        f"Built {manifest['parents']} LADs and {manifest['children']:,} child areas "
        f"across {manifest['child_files']} static files"
    )


if __name__ == "__main__":
    main()
