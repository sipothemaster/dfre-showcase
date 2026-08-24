# Britain's Digital Food Environment

A professional project report and browser-based WebGIS for a national spatial-data study of restaurant and grocery delivery availability across Great Britain. The site presents the full research chain: representative-postcode design, cloud data collection, spatial integration, analysis, and public communication.

Production URL: `https://sipothemaster.github.io/dfre-showcase/`

## What the public site contains

- A compact research architecture covering sampling, API discovery, cloud execution, storage, and production datasets.
- A data-relationship model separating opening-hours-derived availability from observed open-now availability.
- Retailer-owned versus digital delivery platform comparisons for matched grocery services, using Just Eat as the observed platform.
- Spatial findings on deprivation, rurality, and alternative exposure definitions.
- A MapLibre explorer covering 43,064 LSOAs and Scottish Data Zones.

The former Dash application is not embedded or linked. It remains an internal research tool; this repository is the purpose-built public presentation layer.

## Public terminology

Use **digital delivery platforms** as the consistent umbrella term in public-facing analysis. Use **Just Eat** only when identifying the observed platform or a dataset category, and **retailer-owned delivery** for services operated directly by a grocery retailer. Avoid switching between “marketplace delivery” and “digital delivery platforms” for the same concept.

## Architecture

```text
LSOA / Data Zone population-weighted centroid
                    |
                    v
          nearest valid postcode
                    |
                    v
browser network observation -> enriched listing API -> reusable batch client
                    |
                    v
       Cloud Tasks          Cloud Run
       orchestration        collection workers
                    |
                    v
     BigQuery production tables + GCS raw JSON
                    |
                    v
      Python / SQL spatial integration and analysis
                    |
                    v
       Astro report + MapLibre browser explorer
                    |
                    v
          GitHub Pages (no application server)
```

The platform pipeline uses 43,062 unique representative postcodes for 43,064 small areas. Playwright was used to inspect Fetch/XHR responses and identify the enriched postcode listing endpoint. A parameterised Python client was then deployed through Cloud Tasks and Cloud Run, with run manifests, events, diagnostics, and production tables stored in BigQuery and compressed complete responses retained in Cloud Storage.

The production data separates two temporal concepts:

- **Opening-hours-derived availability:** full postcode–restaurant coverage joined to restaurant opening schedules. This represents availability inferred from stated hours, not verified live status.
- **Observed open-now availability:** restaurants observed as open for delivery during four predefined collection windows: weekday afternoon, weekday evening, weekday early hours, and Saturday peak.

## Core data scale

| Dataset | Grain | Production scale |
| --- | --- | ---: |
| Static coverage | Postcode × restaurant | 16,534,508 rows |
| Restaurant profile | Restaurant | 100,850 rows |
| Opening schedules | Restaurant × service × time | Normalised intervals |
| Observed availability | Postcode × window × open restaurant | 30,025,952 rows |
| Direct grocery | Service × LSOA / Data Zone | 6 × 43,064 areas |
| Spatial analysis | LSOA / Data Zone / MSOA | 43,064 / 6,856 areas |

The explorer uses progressive geography loading. A simplified 350-feature LAD overview is loaded first; one of 350 child GeoJSON files is fetched only after a local authority is selected. Metric switching, classification, lookup, and profile rendering happen in the browser, so there are no Dash callbacks or Python requests at runtime.

## Local development

Requires Node.js 22.12 or newer and Python 3.11 or newer.

```sh
npm ci
npm run dev
npm run build
```

Because the Astro project has a GitHub project-page base path, use:

```text
http://localhost:4321/dfre-showcase/
```

## Rebuilding the presentation artifacts

The source repositories are expected to be sibling directories of this repository.

First produce the validated analytical exports:

```sh
python ../delivery-analytics/scripts/export_showcase_retailer_channels.py
python ../delivery-analytics/scripts/export_showcase_core_analysis.py
```

Then synchronise the validated artifacts and rebuild the map assets:

```sh
python scripts/sync_web_exports.py
python scripts/build_map_assets.py
npm run build
```

The map build validates 43,064 unique small-area keys and 350 LAD parent keys before writing output. Asset manifests record scope, byte size and checksums where applicable.

## Adding a future analysis

Each detailed analysis is a content module in `src/content/analyses/`. Adding a Markdown file with the collection schema fields defined in `src/content.config.ts` generates its analysis route. Homepage findings remain deliberately curated in `src/pages/index.astro` and the corresponding presentation components.

SEM and machine-learning work can therefore be added later without restructuring the site. New modules should keep their own claim status, geography, source dates, methods, limitations, and evidence asset. Draft work should remain outside the public collection or use a non-published status.

## Evidence and interpretation boundaries

- One representative postcode is used for each LSOA or Scottish Data Zone.
- Availability describes an observed delivery market, not household behaviour or consumption.
- `Unknown` direct-retailer responses are never converted to `No`.
- “Just Eat only” means the digital delivery platform was observed where the matched retailer-owned service returned `No`; it is evidence of an additional observed channel, not a causal claim that Just Eat created access.
- Deprivation and health results are ecological and non-causal. Health estimates refer to 2024/25, while delivery exposure is a 2026 snapshot.

## Deployment

The workflow in `.github/workflows/deploy.yml` builds the committed static release and deploys it through GitHub Pages. In the GitHub repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**.

No secrets or runtime environment variables are required for the public site.
