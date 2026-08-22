# Britain's Digital Food Environment

An editorial case study and browser-based WebGIS for a national spatial-data project. The site connects four source projects into one public narrative: data collection, cloud processing, statistical analysis, and interactive communication.

Production URL: `https://sipothemaster.github.io/dfre-showcase/`

## What the public site contains

- A concise account of the data-engineering pipeline and its scale.
- Direct-retailer versus Just Eat channel comparisons for matched grocery services.
- Descriptive findings on deprivation, rurality, and alternative exposure definitions.
- A MapLibre explorer covering 43,064 LSOAs and Scottish Data Zones.
- Versioned, area-level downloads with no postcodes, restaurant-level records, raw responses, or credentials.

The former Dash application is not embedded or linked. It remains an internal research tool; this repository is the purpose-built public presentation layer.

## Architecture

```text
source collection + GCP pipeline
             |
             v
validated analytical exports (Python / SQL)
             |
             v
public area-level release (CSV / JSON / GeoJSON)
             |
             v
Astro editorial pages + MapLibre browser explorer
             |
             v
GitHub Pages (no application server)
```

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

## Rebuilding the public data

The source repositories are expected to be sibling directories of this repository.

First produce the validated analytical exports:

```sh
python ../delivery-analytics/scripts/export_showcase_retailer_channels.py
python ../delivery-analytics/scripts/export_showcase_core_analysis.py
```

Then publish the release and rebuild the map artifacts:

```sh
python scripts/sync_web_exports.py
python scripts/build_map_assets.py
npm run build
```

The map build validates 43,064 unique small-area keys and 350 LAD parent keys before writing output. Data manifests record release scope, byte size, and checksums where applicable.

## Adding a future analysis

Each public analysis is a content module in `src/content/analyses/`. Add a Markdown file with the collection schema fields defined in `src/content.config.ts`; Astro generates the analysis route and adds published modules to the homepage register automatically.

SEM and machine-learning work can therefore be added later without restructuring the site. New modules should keep their own claim status, geography, source dates, methods, limitations, and evidence asset. Draft work should remain outside the public collection or use a non-published status.

## Evidence and interpretation boundaries

- One representative postcode is used for each LSOA or Scottish Data Zone.
- Availability describes an observed delivery market, not household behaviour or consumption.
- `Unknown` direct-retailer responses are never converted to `No`.
- “Just Eat only” means the marketplace was observed where the matched direct service returned `No`; it is evidence of an additional observed channel, not a causal claim that Just Eat created access.
- Deprivation and health results are ecological and non-causal. Health estimates refer to 2024/25, while delivery exposure is a 2026 snapshot.

## Deployment

The workflow in `.github/workflows/deploy.yml` builds the committed static release and deploys it through GitHub Pages. In the GitHub repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**.

No secrets or runtime environment variables are required for the public site.
