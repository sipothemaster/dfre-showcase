# HASP explorer design decision log

## 30 September 2026

### Keep the work in `dfre-showcase`

The HASP explorer redesign remains in the existing Astro repository. The same
map assets, import contracts, and presentation layer are reused.

### Keep Astro and the current map implementation

The work is a visual and information-architecture redesign. It does not replace
the framework or create a second analytical pipeline.

### Make the map the primary entry

`/explore/` is the primary shared experience. Users do not need to visit the
existing homepage before reaching the map.

### Reuse selected pipeline and data explanation content

The existing homepage may supply components or copy for a dedicated `About the
data` experience. Reuse must preserve source ownership and avoid duplicating
analytical definitions.

### Follow HASP visual language without cloning one page

The formal guidelines and approved artwork define the identity. The live PPFI
and IMD Explorer supplies useful interface proportions and patterns. Project-
specific map needs and accessibility requirements may justify documented
departures.

### Defer agent instructions and skills

The design documents are the current source of truth. Add only stable,
repository-wide rules to `AGENTS.md` after design approval. Create a repo skill
only if a repeatable HASP design or review workflow emerges.

### Build the first design prototype at `/explore/`

The first local prototype uses the reference explorer's compact header,
control-sidebar proportions, Figtree typography, selected states, rounded
panels, and map overlays. Formal SDR UK colours take precedence over local test
site variants. `Explore map` remains the default view and `About the data`
provides definitions, limitations, pipeline context, and a link to fuller
methods.

## 7 October 2026 — Homepage styling

The user requested HASP visual styling for the homepage while retaining its
headline-led data story, existing copy, section order and analytical results.
`home-hasp.css` scopes the treatment to `body.hasp-story`; the explorer and
other analysis pages keep their existing styles. Use the supplied HASP artwork,
Figtree type, navy/green accents and restrained white/pale panels. Preserve the
scientific chart palettes and their matching legends.

## 7 October 2026 — Explorer release

Use the validated `nutrition_society_v2` dashboard caches for restaurant and
scheduled opening metrics. Counts exclude retail; fast food includes the
original tags plus Chinese, Indian and Desserts. Default to `Opening deliverable
restaurants` at Friday 20:00, label the static measure `Total deliverable
restaurants`, and temporarily hide Iceland from the controls and area profiles.
Retain missing fast-food shares as unavailable when the denominator is zero.

Fit the initial map and every return to the LAD overview to the full imported
Great Britain geometry, including the northern islands. Refit national views
on resize and allow further zooming out without a geographic camera constraint.
