## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Data ownership

This repository is the public presentation layer. Do not create a second
analytical pipeline here.

- `delivery-availability-pipeline` owns platform collection, GCP execution,
  BigQuery production tables and raw-response retention.
- `WebscrapingDeliveryAvailability` owns retailer-specific availability
  collection.
- `delivery-map-dashboard` owns the existing static area/LAD caches and
  scheduled opening-time caches used by the explorer.
- `delivery-analytics` owns analytical definitions, retailer-channel
  classifications, patch construction, regression, SEM and durable model
  outputs.
- `dfre-showcase` may copy validated exports, calculate presentation-only
  summaries, generate web/map assets and render figures. It must not refit a
  model, redefine a classification or silently alter an analytical result.

Generated JSON, CSV and figure assets are build products. Do not edit their
numbers manually. Change or rerun the source-owner export, then rerun the
appropriate showcase import.

## Data import register

Sibling repositories are expected beside this repository under the same
parent directory.

| Public module | Source owner and durable input | Showcase import/build |
| --- | --- | --- |
| Core deprivation/rurality regression and three-panel IMD figure | `delivery-analytics/outputs/web/core_analysis_summary.json` and `02_adjusted_imd_score_predictions.png`, exported from notebook `02` | `python scripts/sync_web_exports.py` |
| GB retailer-channel summary and area classifications | `delivery-analytics/outputs/web/retailer_channel_summary.json` and `retailer_channel_areas.csv` | `python scripts/sync_web_exports.py` |
| England retailer-channel bars | The imported `public/data/v1/retailer_channel_areas.csv` | Generated automatically by `sync_web_exports.py`; standalone: `python scripts/import_retailer_channel_summary.py` |
| England retailer-channel static maps | Analytics area classifications plus `public/map/v1/children/*.geojson` | `python scripts/build_channel_coverage_maps.py` |
| Patch-size distribution and morphology composition | Analytics notebook `06` durable patch-size, composition and KDE-coordinate CSVs | `python scripts/import_grocery_patch_analysis.py` |
| Patch-morphology England maps | Analytics notebook `06` patch membership, retailer classification and England boundaries | `python scripts/build_patch_morphology_maps.py` |
| Spatial robustness: OLS, Rook SEM and Jaccard sensitivity | Analytics notebook `04` durable prediction, diagnostic, contrast and weights-audit CSVs | `python scripts/import_spatial_robustness.py` |
| Explorer static restaurant and channel metrics | `delivery-map-dashboard/data/cache/` plus the imported analytics retailer-channel area CSV | `python scripts/build_map_assets.py` |
| Explorer scheduled day/hour metric | `delivery-map-dashboard/data/cache/opening_by_hour/` and `parent_opening_by_hour/` | `python scripts/build_temporal_map_assets.py` |

### England retailer coverage summary

`src/data/generated/retailer_channel_summary_england.json` is not an
independent analysis. It is a deterministic presentation summary derived from
the validated analytics-owned `retailer_channel_areas.csv`.

The import:

1. validates 43,064 unique GB areas for each displayed comparison;
2. keeps rows whose `geography_code` starts with `E`;
3. validates exactly 33,755 England LSOA 2021 rows;
4. counts each existing `channel_category` and divides by 33,755;
5. preserves `Direct unresolved` as a separate category;
6. records the source file size and SHA-256 in `sourceContract`.

The displayed comparisons are Co-op, Sainsbury's fast and Morrisons fast.
Do not manually remove unresolved rows from the denominator or convert them to
`No`. The component may suppress the unresolved segment visually, but the
generated record must preserve it and the visible bar may therefore total
slightly below 100%.

When the repaired grocery inputs or analytics classification changes, run:

```sh
python ../delivery-analytics/scripts/export_showcase_retailer_channels.py
python scripts/sync_web_exports.py
python scripts/build_channel_coverage_maps.py
python scripts/build_map_assets.py
```

No manual modification of the England summary is required.

### Full public rebuild

After the relevant upstream notebooks and exports have been executed, rebuild
all current presentation artifacts with:

```sh
python scripts/sync_web_exports.py
python scripts/import_grocery_patch_analysis.py
python scripts/import_spatial_robustness.py
python scripts/build_channel_coverage_maps.py
python scripts/build_patch_morphology_maps.py
python scripts/build_map_assets.py
python scripts/build_temporal_map_assets.py
npm run build
```

Every import must validate geography cardinality and key uniqueness. Keep
analysis-owned definitions in the analytics repository, and record the source
contract in generated output whenever practical.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
