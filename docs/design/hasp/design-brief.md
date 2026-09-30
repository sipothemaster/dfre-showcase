# HASP map design brief

Status: draft for implementation and HASP review
Last reviewed: 30 September 2026

## Purpose

Restyle the existing DFRE delivery availability explorer so that it reads as a
Healthy and Sustainable Places Data Service product. Keep the current Astro and
MapLibre implementation, validated data assets, and data ownership boundaries.

The primary user journey starts at `/explore/`. The existing DFRE homepage is
not part of that journey, but its pipeline and methodology components may be
reused from a clearly labelled data and methods view.

## Evidence hierarchy

Use evidence in this order when sources differ:

1. The supplied SDR UK brand guidelines, version 1.3, February 2024.
2. The supplied `HASPDataService_rgb.png` artwork.
3. The live PPFI and IMD Explorer reference implementation.
4. The two supplied dashboard screenshots.
5. A documented project-specific proposal in this folder.

The live reference is a useful implementation example, but it contains colours
that are not in the formal brand palette. Those values must not silently replace
the formal brand tokens.

## Product principles

- Put the map task first. Avoid a portfolio-style or editorial landing page.
- Use the supplied HASP service identity without redrawing, recolouring, or
  distorting it.
- Use Figtree throughout the product interface.
- Keep headings short, functional, and subordinate to the map.
- Keep data definitions, sources, temporal coverage, limitations, citation,
  and funding information reachable from every map state.
- Preserve the existing analytical results and generated assets. A visual
  redesign does not authorise changes to classifications, denominators,
  measures, or map data.
- Use brand colours for product chrome. Use a separate, tested visualisation
  palette for ordered map values and categorical data.

## Proposed information architecture

### Default view: Explore map

The map remains the default and dominant view.

- Fixed or sticky product header.
- Compact left control sidebar on desktop.
- Full available map canvas.
- Current metric, geography, legend, and selection details remain visible.
- Area details may use the existing profile region or a responsive drawer.

### Secondary view: About the data

Follow the interaction pattern used by the PPFI and IMD Explorer: provide a
clear view switch rather than hiding all documentation behind small tooltip
icons. Label it `About the data`.

The view must contain:

- what the explorer measures;
- metric definitions and units;
- geography and representative-postcode design;
- source systems and observation period;
- update or snapshot date;
- limitations and missingness;
- the pipeline at a useful summary level;
- links to fuller methods and analysis;
- suggested citation, acknowledgements, and funding text when confirmed.

The existing homepage components may be reused, but the copy must be selected
for this product context rather than embedding the entire homepage.

## Desktop layout baseline

Use the live reference as the sizing baseline at a 1280 px viewport:

- Header: 84 px observed runtime height, 28 px horizontal padding.
- Logo: 52 px high with automatic width. The supplied artwork renders at about
  180 px wide at this height; never force it into the reference site's 160 px
  bounding box if that changes its aspect ratio.
- Tool title: 24 px / 700, 1.1 line height, -0.02 em tracking.
- Tool subtitle: 18 px / 400, two pixels below the title.
- Sidebar: approximately 282 px overall width with 18 px outer padding.
- Main content starts approximately 300 px from the left edge.
- Sidebar groups: 12 px padding, 12 px bottom gap, 14 px radius.
- Main cards: 16 px padding, 16 px radius.
- Map should consume the remaining viewport width and height after the header.

The supplied dashboard screenshots show other valid compositions, including a
larger left-aligned service logo. For this explorer, use the reference site's
title-left and logo-right header because it gives the map more stable product
context while keeping the service mark visible.

## Responsive behaviour

- Below the desktop breakpoint, collapse the sidebar into a control drawer or
  stacked control region above the map.
- Keep the logo visible, but reduce its height while preserving aspect ratio and
  exclusion space.
- Keep the map at least 60 viewport-height units tall on small screens.
- Present area details and `About the data` as full-width content below the map
  or as an accessible modal/drawer.
- Do not shrink control labels or body copy below an accessible reading size to
  preserve the desktop composition.

## Logo requirements

- Use supplied artwork rather than recreating the service mark.
- Preserve the original aspect ratio.
- Use the depth of the logo semicircle as the minimum clearance guide.
- Prefer white or another high-contrast approved background.
- Do not recolour, distort, redraw, add shapes to, or place the logo on a low
  contrast image.
- Request an SVG version before final release. The supplied transparent PNG is
  suitable for prototyping but is not the preferred long-term web master.

## Accessibility requirements

- Retain visible keyboard focus. The reference uses a 3 px brand-blue outline
  with a 2 px offset.
- Do not rely on colour alone for selected controls, map categories, or area
  states.
- Test map ramps independently of the identity palette.
- Maintain readable contrast for muted helper copy; the reference site's 11 px
  grey helper labels should not be copied where the text is important.
- Respect reduced motion for any decorative brand-shape animation.

## Implementation boundary

This redesign may change Astro markup, components, CSS, icons, and
presentation-only copy. It must not change the data generation scripts,
validated public data, analytical definitions, or source-owner responsibilities
recorded in the repository `AGENTS.md`.

## Open questions for HASP

1. Is this page a core SDR UK communication that must include the full-colour
   UKRI or UKRI-ESRC lockup described in the brand guidelines?
2. Should the product be fully HASP branded or co-branded with DFRE and the
   researcher/project identity?
3. What is the approved public product title and subtitle?
4. Should the HASP logo link to `https://hasp.ac.uk/`?
5. Can HASP provide the service logo as SVG and the approved Figtree webfont
   files?
6. Is there approved citation, funding, contact, and data-controller copy?
7. Are the live reference's non-guideline purple, orange, and lavender values
   deliberate additions to the digital palette or local implementation choices?
8. Who gives final visual approval, and which browsers and accessibility level
   form the acceptance baseline?
