"""Publish validated analytics exports into the static showcase release."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from import_retailer_channel_summary import write_summary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy(source: Path, destination: Path) -> dict:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": destination.as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    }


def parse_args() -> argparse.Namespace:
    showcase_root = Path(__file__).resolve().parents[1]
    analytics_root = showcase_root.parent / "delivery-analytics"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analytics-web-directory",
        type=Path,
        default=analytics_root / "outputs" / "web",
    )
    parser.add_argument("--showcase-root", type=Path, default=showcase_root)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.analytics_web_directory
    build_data = args.showcase_root / "src" / "data" / "generated"
    public_data = args.showcase_root / "public" / "data" / "v1"

    files = []
    for name in ["core_analysis_summary.json", "retailer_channel_summary.json"]:
        files.append(copy(source / name, build_data / name))
        files.append(copy(source / name, public_data / name))
    files.append(
        copy(
            source / "retailer_channel_areas.csv",
            public_data / "retailer_channel_areas.csv",
        )
    )
    files.append(
        copy(
            source / "02_adjusted_imd_score_predictions.png",
            args.showcase_root
            / "public"
            / "images"
            / "analysis"
            / "02_adjusted_imd_score_predictions.png",
        )
    )

    england_summary = build_data / "retailer_channel_summary_england.json"
    write_summary(public_data / "retailer_channel_areas.csv", england_summary)
    files.append(
        {
            "path": england_summary.as_posix(),
            "bytes": england_summary.stat().st_size,
            "sha256": sha256(england_summary),
        }
    )

    for item in files:
        path = Path(str(item["path"]))
        if path.is_absolute():
            item["path"] = path.relative_to(args.showcase_root).as_posix()

    manifest = {
        "release": "v1",
        "scope": "Public area-level DFRE showcase artifacts",
        "privacy": "No postcodes, restaurant-level records or credentials",
        "files": files,
    }
    manifest_path = public_data / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Published {len(files)} artifacts and {manifest_path}")


if __name__ == "__main__":
    main()
