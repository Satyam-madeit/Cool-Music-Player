---
name: Kuro Sound Lab
colors:
  surface: '#131316'
  surface-dim: '#131316'
  surface-bright: '#39393c'
  surface-container-lowest: '#0e0e11'
  surface-container-low: '#1b1b1e'
  surface-container: '#1f1f22'
  surface-container-high: '#2a2a2d'
  surface-container-highest: '#353438'
  on-surface: '#e4e1e6'
  on-surface-variant: '#e8bcb9'
  inverse-surface: '#e4e1e6'
  inverse-on-surface: '#303033'
  outline: '#ae8784'
  outline-variant: '#5e3f3d'
  surface-tint: '#ffb3ae'
  primary: '#ffb3ae'
  on-primary: '#68000b'
  primary-container: '#ff5352'
  on-primary-container: '#5c0009'
  inverse-primary: '#c0001e'
  secondary: '#b5c4ff'
  on-secondary: '#00297a'
  secondary-container: '#005cfa'
  on-secondary-container: '#e8ebff'
  tertiary: '#f3c000'
  on-tertiary: '#3d2e00'
  tertiary-container: '#d2a500'
  on-tertiary-container: '#4f3d00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad7'
  primary-fixed-dim: '#ffb3ae'
  on-primary-fixed: '#410004'
  on-primary-fixed-variant: '#930014'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b5c4ff'
  on-secondary-fixed: '#00174d'
  on-secondary-fixed-variant: '#003dab'
  tertiary-fixed: '#ffdf91'
  tertiary-fixed-dim: '#f3c000'
  on-tertiary-fixed: '#241a00'
  on-tertiary-fixed-variant: '#594400'
  background: '#131316'
  on-background: '#e4e1e6'
  surface-variant: '#353438'
  paper-white: '#f5f4ef'
  paper-cream: '#eae7dc'
  charcoal-dark: '#0a0a0c'
  surface-panel: '#17181c'
  surface-border: '#282a30'
  muted-silver: '#8e919e'
  obi-lavender: '#8d79b8'
typography:
  display-hero:
    fontFamily: Space Grotesk
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.04em
  display-hero-mobile:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.03em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-data-lg:
    fontFamily: Space Mono
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: 0.04em
  label-data-md:
    fontFamily: Space Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.06em
  label-stamp:
    fontFamily: Space Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.1em
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system targets discerning audiophiles, digital archivism enthusiasts, and music collectors who view listening as an intentional ritual rather than background noise. The personality balances uncompromising technical precision with tactile, artisanal graphic nostalgia. It draws inspiration from Japanese vinyl Obi strips, 1980s Mecha animation artboards, and limited-edition cassette and CD packaging.

The aesthetic fuses **Brutalism** and **Tactile Minimalism**. It relies on solid monochromatic color blocking, sharp rectangular divisions, dense typographic metadata, and purposeful pops of chromatic energy (crimson lacquer, cyber cobalt, and screenprint yellow). The UI rejects generic floating blur cards in favor of tangible physical packaging cues: crisp ruled dividing lines, stamp-like badges, technical format parameters (FLAC 24-bit/96kHz, MP3 V0), and modular editorial grids. The experience evokes operating a boutique Japanese hi-fi console or unboxing an imported physical audio archive.

## Colors

The palette is anchored in an uncompromising deep matte charcoal (`#101013` and `#0a0a0c`) that prevents glare during focused nighttime listening while providing a rich ground for colorful vinyl cover art.

- **Primary (`#ff2b38`)**: Searing lacquer crimson drawn directly from Japanese editorial headers and vinyl warning seals. Reserved for high-priority play states, recording flags, and key interactive focal points.
- **Secondary (`#1261ff`)**: Electric cyber cobalt inspired by retro mechanical packaging and digital synthesis interfaces. Used for active scrubbing states, audio stream routing, and digital bit-depth tags.
- **Tertiary (`#ffca18`)**: Warm screenprint ochre-yellow. Emulates vintage caution labels and format highlights (e.g., Hi-Res Lossless markers, loop toggles).
- **Paper Accents (`#f5f4ef`, `#eae7dc`)**: Unbleached print whites applied to high-legibility track titles, typographic metadata columns, and cassette inlay tabs.
- **Obi Lavender (`#8d79b8`)**: Inspired by archival Japanese spine banners; serves as an accent for library categorization, catalog numbers, and editorial badges.

## Typography

The typographic hierarchy is split across three distinct functional roles:

1. **Display & Headings (Space Grotesk)**: Architectural, geometric, and uncompromising. It brings retro-futurist magazine impact to artist titles, release names, and view headers. Uppercase treatments with tight letter-spacing reinforce structural packaging grids.
2. **Body & Catalog Data (Hanken Grotesk)**: Clean, contemporary grotesque with exceptional legibility across dense track listings, liner notes, and settings panels.
3. **Audio Metadata & Stamps (Space Mono)**: Monospaced machine type engineered for bitrates, sample frequencies (e.g., `44.1kHz / 16bit`), track durations, catalog matrix numbers (`CAT: YZY-091107`), and timecodes. This keeps numerical values tabular and jitter-free during real-time playback.

## Layout & Spacing

The layout is built upon a modular editorial cassette grid that mirrors physical media sleeves.

- **Desktop (Windows/Cross-Platform)**: 12-column modular grid with `1.5rem` gutters and `2rem` outer margins. The desktop layout splits into three distinct functional panels:
  - **Left Rail (Vertical Obi Strip)**: A fixed 80px to 220px vertical panel for global playback status, format badges (`FLAC`), library tabs, and stamp-like metadata.
  - **Center Stage**: Adaptive column grid housing current vinyl artwork, spectrum analyzers, and interactive lyrics/chords.
  - **Right Sidebar**: Dense tracklist queue and transport metadata matrix.
- **Mobile / Responsive Reflow**: Condenses to a single fluid column with a strict `1rem` margin. The Obi strip transitions into an anchored top utility bar or condensed bottom sheet player.
- **Rhythm**: Everything conforms strictly to a 4px/8px baseline grid. Padding within modules is tight and architectural (`space-sm` and `space-md`), preserving dense informational density without clutter.

## Elevation & Depth

This system avoids soft, floating dropshadows and blurred glass surfaces. Depth is established through **solid structural borders**, **tonal surface containment**, and **mechanical layering**:

- **Borders & Dividers**: Crisp `1px` solid outlines using `surface-border` (`#282a30`) delineate every control group, album jacket slot, and parameter table.
- **Layer Stacking**: Elevated elements (such as modal track inspectors, contextual menus, or hovering tooltips) use pure flat black (`#0a0a0c`) fills with an outer `1px` high-contrast outline (`#f5f4ef` or `#ff2b38`) accompanied by a hard-edge offset shadow: `3px 3px 0px #000000`.
- **Inverted Surfaces**: Interactive selections and active queue items invert into pure paper white (`#f5f4ef`) backgrounds with stark solid black text, providing immediate physical feedback like a stamped catalog card.

## Shapes

The shape language is strictly **Sharp (`0`)**. 

All buttons, album artwork containers, sliders, progress bars, and modal windows feature crisp 90-degree right angles (`0px` border-radius). This zero-radius mandate echoes industrial hi-fi equipment, cassette j-cards, vinyl sleeves, and printed tech schematics. Micro-tags and stamps may incorporate beveled or chamfered 45-degree edge clips on individual corners for technical cues, but soft rounded pill forms are prohibited.

## Components

### Buttons & Transport Controls
- **Primary Play / Pause Action**: Solid rectangular blocks with high-impact color fills (`primary_color_hex` or `paper-white`). Active pressed state shifts position by `1px 1px` with an inverted color scheme.
- **Secondary Actions (Shuffle, Repeat, Format Select)**: Outlined boxes with `1px solid surface-border`. Iconography is accompanied by micro monospace abbreviations (`SHF`, `RPT`, `M/S`).
- **Tactile Icons**: Minimalist stroke icons with distinct geometric or subtle hand-drawn graphic flair, paired alongside Japanese kanji or expressive monochrome glyphs (e.g., `再生` for play, `停止` for stop).

### Chips & Format Badges (Obi Tags)
- **Audio Spec Tags**: Dense tabular badges displaying `FLAC 96/24`, `MP3 320`, or `STEREO`. Outlined with `1px solid`, using `label-stamp` typography.
- **Status Indicators**: Solid background fills in `tertiary_color_hex` (Ochre) or `secondary_color_hex` (Cobalt) to communicate dynamic stream health and DAC connection state.

### Tracklist & Tables
- **Rows**: Separated by hairline dividers (`1px solid #282a30`).
- **Index Numbers**: Displayed in two-digit monospaced format (`01`, `02`, `12`).
- **Active State**: Inverted contrast row—background floods to `#f5f4ef` with `#101013` typography, instantly highlighting the active track across expansive desktop monitors.

### Sliders & Scrubbers (Progress & Volume)
- **Track Rail**: Flat `2px` or `4px` solid border line.
- **Filled Track**: Solid fill in `secondary_color_hex` (Cobalt) or `primary_color_hex` (Crimson).
- **Playhead Thumb**: Sharp vertical needle or solid `8px x 14px` unrounded rectangle thumb that slides along the rail. Hovering reveals a monospace timecode tooltip.

### Input Fields & Search
- **Search Bar**: Dark surface (`#17181c`) boxed by `1px solid surface-border`. Focus state transitions border to stark white (`#f5f4ef`) or cyber cobalt. Prefix icon features a stamped prompt symbol (`>_` or `REC //`).

### Album Art Presentation & Packaging Cards
- **Art Framing**: Album artwork renders unrounded inside a 1px border container. An optional vertical side strip (inspired by Japanese Obi spines) overlays on the left margin carrying the album catalog code, release date, and country press details.