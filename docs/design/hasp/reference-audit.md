# HASP reference interface audit

Observed URL: <https://imd-ppfi-test-gcege7ghhhcedkex.uksouth-01.azurewebsites.net/>

Observed: 30 September 2026
Viewport used for exact runtime measurements: 1280 × 720 CSS pixels

## What to learn from the reference

The reference is a task-focused data explorer. Its visual hierarchy is defined
by a compact product header, fixed control sidebar, large map surface, Figtree
typography, pale blue selected states, rounded white control groups, and small
map overlays. The map and controls carry the interface; the title does not act
as a hero element.

## Observed runtime measurements

| Element | Observed specification |
| --- | --- |
| Header | 84 px high; 28 px horizontal padding; bottom border |
| Header title | 24 px / 700; 26.4 px line height; -0.48 px tracking |
| Header subtitle | 18 px / 400; muted navy |
| Header logo | 160 × 52 px observed box |
| Sidebar | 282 px wide; white; 18 px internal edge padding |
| Main region | Starts at x = 282 px; 18 px horizontal content padding |
| Sidebar group | 231 px typical width; 12 px padding; 14 px radius |
| Selected nav option | 205 × 35 px; 8 × 10 px padding; 10 px radius |
| Map view controls | 13 px / 500 option text; 12 px muted label |
| Map canvas | x = 300 px; width = 962 px; observed height = 509 px |
| About main heading | 24 px / 700 |
| About section heading | 16 px / 700 |
| Information card | 14 × 18 px padding; 8 px radius; 4 px left accent |
| Divider | pale two-pixel rendered rule; restrained vertical spacing |

The source stylesheet declares a 96 px navbar, while runtime measurement on the
loaded page was 84 px. Treat the runtime size as the closer reference for this
prototype and avoid assuming every source rule is active.

## Visual language

- White and pale lavender surfaces dominate.
- Navy provides almost all typography and strong UI identity.
- Border contrast is low: navy at approximately 15–18% opacity.
- Cards use 8–16 px radii according to scale.
- Structural cards avoid shadows; floating map overlays use a very small shadow.
- Uppercase labels are limited to small sidebar categories.
- Selected navigation uses a pale-blue rounded rectangle and a visible selected
  radio control.
- Prose pages use compact headings, short rules, and two-column information
  cards rather than oversized display typography.

## Relevant content pattern

The reference includes an `About this tool` view alongside its map views. It
contains:

- an explanation of the tool's purpose;
- measure and domain definitions;
- methodology links;
- expandable use instructions;
- data sources and full dataset link;
- suggested citation; and
- funding information.

This is the strongest reference for the proposed `About the data` view in the
DFRE explorer.

## Intentional differences for this project

- The DFRE explorer defaults to the map and keeps documentation secondary.
- The formal SDR UK palette takes precedence where the test site uses local
  purple, orange, or lavender values.
- The supplied logo's aspect ratio is preserved instead of forcing the observed
  logo box dimensions.
- The existing MapLibre interaction and validated data assets are retained.
- A responsive control drawer will be designed explicitly rather than copying
  the reference's desktop-fixed layout without adaptation.
