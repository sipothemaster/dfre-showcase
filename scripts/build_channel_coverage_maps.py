"""Build static small-area channel-coverage maps for the public report."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


EXPECTED_AREAS = 43_064
ENGLAND_PREFIX = "E"
COMPARISONS = {
    "coop": "coop.png",
    "sainsburys_fast": "sainsburys-fast.png",
    "morrisons_fast": "morrisons-fast.png",
}
CATEGORY_COLOURS = {
    "Both channels": "#6f746f",
    "Direct only": "#a09c93",
    "Just Eat only": "#b6412f",
    "Neither observed": "#ddd8cc",
}


def load_small_areas(children_root: Path) -> gpd.GeoDataFrame:
    paths = sorted(children_root.glob("*.geojson"))
    if not paths:
        raise FileNotFoundError(f"No child GeoJSON files found in {children_root}")

    frames = [gpd.read_file(path) for path in paths]
    areas = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        geometry="geometry",
        crs=frames[0].crs,
    )
    if len(areas) != EXPECTED_AREAS or areas["id"].nunique() != EXPECTED_AREAS:
        raise ValueError(
            f"Expected {EXPECTED_AREAS:,} unique areas, found "
            f"{len(areas):,} rows / {areas['id'].nunique():,} ids"
        )
    return areas[["id", "geometry"]].to_crs("EPSG:27700")


def build_maps(
    map_root: Path,
    channel_csv: Path,
    output_root: Path,
) -> None:
    areas = load_small_areas(map_root / "children")
    england_areas = areas.loc[areas["id"].str.startswith(ENGLAND_PREFIX)].copy()
    parents = gpd.read_file(map_root / "parents.geojson").to_crs("EPSG:27700")
    parents["geometry"] = parents.geometry.make_valid()
    england_outline = parents.loc[
        parents["id"].str.startswith(ENGLAND_PREFIX),
        ["geometry"],
    ].dissolve()
    channels = pd.read_csv(channel_csv, dtype=str)

    bounds = england_outline.total_bounds
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x_pad = width * 0.025
    y_pad = height * 0.015
    output_root.mkdir(parents=True, exist_ok=True)

    for comparison, filename in COMPARISONS.items():
        categories = channels.loc[
            channels["comparison"] == comparison,
            ["geography_code", "channel_category"],
        ]
        if len(categories) != EXPECTED_AREAS:
            raise ValueError(
                f"Expected {EXPECTED_AREAS:,} {comparison} rows, found {len(categories):,}"
            )

        england_categories = categories.loc[
            categories["geography_code"].str.startswith(ENGLAND_PREFIX)
        ]
        mapped = england_areas.merge(
            england_categories,
            left_on="id",
            right_on="geography_code",
            how="inner",
            validate="one_to_one",
        )
        if len(mapped) != len(england_areas):
            raise ValueError(f"Geography mismatch for {comparison}")

        figure, axis = plt.subplots(figsize=(5.4, 6.8))
        figure.patch.set_alpha(0)
        axis.set_facecolor("none")

        for category, colour in CATEGORY_COLOURS.items():
            subset = mapped.loc[mapped["channel_category"] == category]
            subset.plot(
                ax=axis,
                color=colour,
                edgecolor="none",
                linewidth=0,
                antialiased=False,
            )

        england_outline.boundary.plot(
            ax=axis,
            color="#8c8b82",
            linewidth=0.28,
            alpha=0.8,
        )
        axis.set_xlim(bounds[0] - x_pad, bounds[2] + x_pad)
        axis.set_ylim(bounds[1] - y_pad, bounds[3] + y_pad)
        axis.set_aspect("equal")
        axis.axis("off")
        figure.savefig(
            output_root / filename,
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.02,
            transparent=True,
        )
        plt.close(figure)


def parse_args() -> argparse.Namespace:
    showcase_root = Path(__file__).resolve().parents[1]
    analytics_root = showcase_root.parent / "delivery-analytics"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--map-root",
        type=Path,
        default=showcase_root / "public" / "map" / "v1",
    )
    parser.add_argument(
        "--channel-csv",
        type=Path,
        default=analytics_root / "outputs" / "web" / "retailer_channel_areas.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=showcase_root / "public" / "images" / "channel-coverage",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_maps(arguments.map_root, arguments.channel_csv, arguments.output_root)
