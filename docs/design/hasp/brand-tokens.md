# HASP brand and interface tokens

Status: draft implementation specification
Last reviewed: 30 September 2026

## Typography

The formal brand font is Figtree.

```css
--font-sans: "Figtree", "Helvetica Neue", Arial, sans-serif;
--weight-regular: 400;
--weight-medium: 500;
--weight-bold: 700;
```

- Headings: Figtree Bold. Keep them short.
- Optional emphasis inside headings: Figtree Bold Italic.
- Body: Figtree Regular, Medium, or Bold, with matching italics where needed.
- Formal fallback: Helvetica Neue or Arial.

### Reference interface type scale

| Role | Size | Weight | Other |
| --- | ---: | ---: | --- |
| Product title | 24 px | 700 | 1.1 line height; -0.02 em tracking |
| Product subtitle | 18 px | 400 | muted navy |
| Main view heading | 24 px | 700 | functional page heading |
| Section heading | 16 px | 700 | short sentence case |
| Sidebar category | 12 px | 700 | uppercase; 0.04 em tracking |
| Control option | 16 px | 500 | sentence case |
| Body | 16 px | 400 | use about 1.5 to 1.7 line height for prose |
| Accordion summary | 14 px | 600 | sentence case |
| Map overlay title | 13 px | 600 | compact overlay only |
| Map legend | 12 px | 400 | title uses 600 |
| Map legend endpoints | 11 px | 400 | secondary values only |
| Helper copy | 11–12 px | 400 | use 12 px for material instructions |

## Formal SDR UK palette

These values come from the supplied brand guidelines and are the primary source
of truth.

| Token | Value | Intended use |
| --- | --- | --- |
| `--sdr-navy` | `#24226F` | Primary text, strong surfaces, identity |
| `--sdr-grey` | `#B8BCD1` | Supporting graphics and borders |
| `--sdr-green` | `#03CEA3` | Brand shape and positive highlight |
| `--sdr-orange` | `#FF8F42` | Brand shape and selective accent |
| `--sdr-light-grey` | `#E2E5F3` | Pale surfaces and brand shapes |
| `--sdr-blue` | `#1877CF` | Links, focus, informative accent |
| `--sdr-dark-grey` | `#8C91A8` | Secondary graphics and muted elements |
| `--sdr-white` | `#FFFFFF` | Primary background and inverse text |
| `--hasp-green` | `#0B5126` | HASP service identifier; text/highlight/background |

The guidelines state that the service identifying colours pass AAA and may be
used for text, highlights, or backgrounds. Verify actual foreground/background
pairs in the implemented UI rather than treating that statement as approval for
every combination.

## Reference implementation additions

The live PPFI and IMD Explorer uses the following extra values. They are
evidence of a digital implementation, not confirmed core brand tokens.

| Reference token | Value | Decision for this project |
| --- | --- | --- |
| `--reference-blue` | `#7CC6FE` | May inform focus/selected surfaces |
| `--reference-purple` | `#8789C0` | Do not adopt as core without confirmation |
| `--reference-orange` | `#F06449` | Prefer formal `#FF8F42` until confirmed |
| `--reference-page-bg` | `#E2E4FF` | Prefer formal light grey for first prototype |
| `--reference-border` | `rgba(36, 34, 111, 0.15)` | Adopt for product chrome |
| `--reference-muted` | `rgba(36, 34, 111, 0.75)` | Adopt where contrast remains sufficient |
| `--reference-hover` | `rgba(124, 198, 254, 0.20)` | Adopt for hover/selected background |

## Recommended semantic tokens

```css
:root {
  --color-text: #24226f;
  --color-text-strong: #1a1a2e;
  --color-text-muted: rgba(36, 34, 111, 0.75);
  --color-link: #0b5126;
  --color-link-hover: #ff8f42;
  --color-page: #e2e5f3;
  --color-surface: #ffffff;
  --color-border: rgba(36, 34, 111, 0.15);
  --color-focus: #1877cf;
  --color-selection: rgba(124, 198, 254, 0.20);

  --radius-control: 10px;
  --radius-select: 12px;
  --radius-sidebar-group: 14px;
  --radius-panel: 16px;
  --radius-map-overlay: 8px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 18px;
  --space-6: 28px;

  --header-height-desktop: 84px;
  --sidebar-width-desktop: 282px;
}
```

## Component specifications from the reference

### Product header

- White to very pale blue horizontal background treatment.
- One-pixel bottom border using the translucent navy border token.
- 28 px horizontal padding.
- Title and subtitle aligned left; service logo aligned right.
- Observed logo box: 160 × 52 px. For the supplied logo, set only 52 px height
  and allow its approximately 180 px natural width.

### Sidebar group

- White background.
- One-pixel translucent navy border.
- 14 px radius.
- 12 px internal padding and 12 px bottom gap.
- Uppercase 12 px / 700 group label with 0.04 em tracking.
- Helper copy in grey, with six pixels below it before options.

### Sidebar option

- 8 px vertical and 10 px horizontal padding.
- 10 px radius.
- 10 px gap between control and text.
- 16 px / 500 label.
- Pale blue hover and selected background.
- Selected state must include the checked control and not rely only on colour.

### Main panel

- White background.
- One-pixel translucent navy border.
- 16 px radius and 16 px padding.
- Avoid decorative shadows for structural cards.

### Map overlays

- White at 94–96% opacity.
- One-pixel navy border at about 18% opacity.
- 8 px radius.
- Small shadow around `0 1px 3px rgba(0,0,0,.08)`.
- Map title: centred at top, 13 px / 600, 5 × 12 px padding.
- Legend: bottom-right, minimum 160 px, 8 × 10 px padding, 12 px type.
- Popup: 8 × 10 px padding, 8 px radius, restrained 2 px / 6 px shadow.

## Map colour rule

Do not use the formal identity palette as a complete map scale. Each continuous
metric needs an ordered ramp with distinguishable steps, suitable contrast with
boundaries and labels, and a clear no-data colour. Each categorical channel
state needs labels or patterns in addition to colour where ambiguity is likely.

The first visual prototype may derive map ramps from HASP green, SDR blue, or
navy, but the map palette remains a visualisation system rather than a set of
brand tokens.

## Decorative shapes

The guidelines describe the separated geometric shapes as symbols for data
that can be rearranged to create something new.

- They may be used sparingly in an empty state, about view, or footer.
- They must not compete with the map or resemble map controls.
- Use approved compositions or supplied artwork; do not reconstruct the logo.
- Any animation must respect reduced-motion preferences.
