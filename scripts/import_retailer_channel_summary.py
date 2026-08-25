"""Build the England retailer-channel summary from the validated area export.

The channel classification is owned by ``delivery-analytics``. This script
only applies the England geography filter and produces presentation counts and
percentages for the three retailer comparisons shown on the homepage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


EXPECTED_GB_AREAS = 43_064
EXPECTED_ENGLAND_AREAS = 33_755
COMPARISONS = ["coop", "sainsburys_fast", "morrisons_fast"]
CATEGORIES = [
    "Both channels",
    "Direct only",
    "Just Eat only",
    "Neither observed",
    "Direct unresolved",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_summary(source: Path) -> dict[str, object]:
    rows = read_rows(source)
    required = {"geography_code", "comparison", "channel_category"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - (set(rows[0]) if rows else set()))
        raise ValueError(f"Missing required retailer-channel fields: {missing}")

    comparisons = []
    for comparison in COMPARISONS:
        comparison_rows = [row for row in rows if row["comparison"] == comparison]
        geography_codes = [row["geography_code"] for row in comparison_rows]
        if (
            len(comparison_rows) != EXPECTED_GB_AREAS
            or len(set(geography_codes)) != EXPECTED_GB_AREAS
        ):
            raise ValueError(
                f"Expected {EXPECTED_GB_AREAS:,} unique GB areas for {comparison}, "
                f"found {len(comparison_rows):,} rows / "
                f"{len(set(geography_codes)):,} geography codes"
            )

        england_rows = [
            row for row in comparison_rows if row["geography_code"].startswith("E")
        ]
        if len(england_rows) != EXPECTED_ENGLAND_AREAS:
            raise ValueError(
                f"Expected {EXPECTED_ENGLAND_AREAS:,} England LSOAs for "
                f"{comparison}, found {len(england_rows):,}"
            )

        counts = Counter(row["channel_category"] for row in england_rows)
        unexpected = sorted(set(counts) - set(CATEGORIES))
        if unexpected:
            raise ValueError(f"Unexpected channel categories: {unexpected}")
        if sum(counts.values()) != EXPECTED_ENGLAND_AREAS:
            raise ValueError(f"Category counts do not reconcile for {comparison}")

        comparisons.append(
            {
                "comparison": comparison,
                "categories": [
                    {
                        "category": category,
                        "count": counts.get(category, 0),
                        "percent": round(
                            counts.get(category, 0) / EXPECTED_ENGLAND_AREAS * 100,
                            2,
                        ),
                    }
                    for category in CATEGORIES
                ],
            }
        )

    return {
        "schemaVersion": 1,
        "geography": (
            f"{EXPECTED_ENGLAND_AREAS:,} England LSOA 2021 "
            "representative-postcode markets"
        ),
        "sourceContract": {
            "owner": "delivery-analytics",
            "upstreamFile": "outputs/web/retailer_channel_areas.csv",
            "localImportedFile": "public/data/v1/retailer_channel_areas.csv",
            "bytes": source.stat().st_size,
            "sha256": sha256(source),
            "filter": "geography_code begins with E",
            "denominator": EXPECTED_ENGLAND_AREAS,
            "unknownHandling": (
                "Direct unresolved remains a separate category and is not "
                "converted to Direct only or Neither observed."
            ),
        },
        "comparisons": comparisons,
    }


def write_summary(source: Path, output: Path) -> None:
    payload = build_summary(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    showcase_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=showcase_root
        / "public"
        / "data"
        / "v1"
        / "retailer_channel_areas.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=showcase_root
        / "src"
        / "data"
        / "generated"
        / "retailer_channel_summary_england.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_summary(args.input.resolve(), args.output.resolve())
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
