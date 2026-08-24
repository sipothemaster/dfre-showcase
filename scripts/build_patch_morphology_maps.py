"""Build England maps from Notebook 06's durable patch-membership export."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RETAILERS = {
    "coop": "coop.png",
    "sainsburys": "sainsburys-fast.png",
    "morrisons": "morrisons-fast.png",
}
DIRECT_STATES = {"Both", "Direct only"}
MAP_COLOURS = {
    "Fill-in": "#356f78",
    "Edge expansion": "#b6412f",
    "Independent island": "#c79a54",
    "Direct coverage": "#b9bcb6",
    "Other areas": "#dedacf",
}


def build_maps(analytics_root: Path, output_root: Path) -> None:
    boundary_path = (
        analytics_root
        / "data"
        / "external"
        / "geography"
        / "ew_lsoa_2021_bgc_v5.geojson"
    )
    classification_path = (
        analytics_root
        / "data"
        / "processed"
        / "grocery_delivery"
        / "lsoa_grocery_platform_comparison_long.csv"
    )
    membership_path = (
        analytics_root
        / "data"
        / "processed"
        / "grocery_delivery"
        / "justeat_only_patch_membership.csv"
    )

    boundaries = gpd.read_file(boundary_path)
    boundaries = (
        boundaries.loc[
            boundaries["LSOA21CD"].str.startswith("E", na=False),
            ["LSOA21CD", "geometry"],
        ]
        .rename(columns={"LSOA21CD": "geo_code"})
        .to_crs("EPSG:27700")
    )
    boundaries["geometry"] = boundaries.geometry.make_valid()
    classification = pd.read_csv(classification_path, dtype=str)
    membership = pd.read_csv(membership_path, dtype=str)

    if boundaries["geo_code"].duplicated().any():
        raise ValueError("Duplicate LSOA display boundaries")
    if classification.duplicated(["retailer", "geo_code"]).any():
        raise ValueError("Duplicate retailer-LSOA classification keys")
    if membership.duplicated(["retailer", "geo_code"]).any():
        raise ValueError("Duplicate retailer-LSOA patch membership keys")

    england_outline = boundaries[["geometry"]].dissolve()
    bounds = england_outline.total_bounds
    x_pad = (bounds[2] - bounds[0]) * 0.025
    y_pad = (bounds[3] - bounds[1]) * 0.015
    output_root.mkdir(parents=True, exist_ok=True)

    for retailer, filename in RETAILERS.items():
        states = classification.loc[
            classification["retailer"].eq(retailer),
            ["geo_code", "category"],
        ]
        patch_types = membership.loc[
            membership["retailer"].eq(retailer),
            ["geo_code", "patch_type_length_50pct"],
        ]
        mapped = (
            boundaries.merge(states, on="geo_code", how="left", validate="one_to_one")
            .merge(patch_types, on="geo_code", how="left", validate="one_to_one")
        )
        if mapped[["category"]].isna().any().any():
            raise ValueError(f"Missing channel states for {retailer}")

        mapped["map_state"] = mapped["patch_type_length_50pct"]
        context_mask = mapped["map_state"].isna()
        mapped.loc[context_mask, "map_state"] = mapped.loc[
            context_mask, "category"
        ].map(
            lambda category: (
                "Direct coverage" if category in DIRECT_STATES else "Other areas"
            )
        )

        figure, axis = plt.subplots(figsize=(5.4, 6.8))
        figure.patch.set_alpha(0)
        axis.set_facecolor("none")
        for state, colour in MAP_COLOURS.items():
            subset = mapped.loc[mapped["map_state"].eq(state)]
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analytics-root",
        type=Path,
        default=showcase_root.parent / "delivery-analytics",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=showcase_root / "public" / "images" / "patch-morphology",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build_maps(arguments.analytics_root.resolve(), arguments.output_root.resolve())
