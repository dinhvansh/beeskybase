# BeeSky design tokens

One token set drives every BeeSky surface: the two desktop apps
(`beesky/gui.py`, `beesky/agent_gui.py` — tokens in
`beesky/ui_theme.py`, rounded rendering in `beesky/rounded.py`)
and the two web dashboards (`beesky/web/dashboard.html`,
`beesky/cloud/dashboard.html` — the same values as CSS custom
properties). Change a token here and in its code home together.

## Provenance

The interaction rules below (consistent radius scale, visible
hover/pressed feedback on every clickable element, a visible
focus ring for keyboard users, deep-black surfaces with high
text contrast, generous click targets) were adapted from the
**UI/UX Pro Max** skill guidance
(`~/workspace/custom-skills/ui-ux-pro-max-core`) during the
v0.17 overhaul, mapped onto the existing BeeSky brand — the
palette and type below predate that pass and were **not**
changed by it.

## Colour (deep black, 7:1 text contrast)

| Token | Value | Use |
|---|---|---|
| `BG` | `#0B0B0D` | window / page background |
| `PANEL` | `#15151A` | solid fallback + mostly-solid data surfaces (Treeview) |
| `PANEL2` | `#1C1C22` | solid fallback for fields, hover surfaces |
| `BORDER` | `#26262E` | solid-fallback hairline borders |
| `TEXT` | `#F2F2F3` | primary text (≈15:1 on BG, ≈14:1 on PANEL) |
| `MUTED` | `#9CA3AF` | secondary text (≈7:1 on BG) |
| `ACCENT` | `#F5D800` | BeeSky yellow — primary actions, selection |
| `ACCENT_TEXT` | `#141414` | text on the accent |
| `OK` / `WARN` / `BAD` | `#34D399` / `#FBBF24` / `#F87171` | status tones |

Brand colours are fixed: yellow `#F5D800` on near-black. (The
logo master's own yellow is `#F4D600`; UI surfaces use `#F5D800`.)

## Type

Preferred family **Segoe UI** (Windows), falling back through
Helvetica Neue / Noto Sans / DejaVu Sans. Scale (pt): title 19
bold, section 12 bold, body 11, small 10, stat value 24 bold.

## Radius — one scale everywhere (v0.17)

| Token | Value | Applies to |
|---|---|---|
| `RADIUS_CARD` / `--radius-card` | **16px** | cards, panels, table wrappers, dialogs |
| `RADIUS_WIDGET` / `--radius-widget` | **12px** | buttons, text inputs, selects, nav items, icon chips, heat tiles |
| `RADIUS_PILL` / `--radius-pill` | **999px** (fully round) | status pills, severity chips, inline code chips |

No other radius values are used. A perfect circle (the online
dot on the web dashboards, `border-radius: 50%`) is the pill
token's special case, not a fourth value.

Desktop note: ttk cannot draw border-radius, so the desktop
widgets are rendered on `tk.Canvas` by `beesky/rounded.py`
(`RoundedCard` 16, `RoundedButton`/`RoundedEntry` 12,
`RoundedPill` half-height). Data surfaces stay square by design:
the results Treeview and the detail text sit *inside* rounded
cards, like a table inside a rounded web panel.

## Interaction feedback — every clickable element

- **Hover** lightens the surface (accent `#F5D800` → `#FFE14D`;
  ghost/panel2 → `#26262E`; danger ghost → `#2A1A1A`).
- **Pressed** darkens (accent → `#D9BE00`; ghost → `PANEL`;
  danger ghost → `#2A1515`). Releasing the pointer outside the
  element cancels the click.
- **Keyboard focus** draws a visible 2px ring inset in the
  element (accent outline on ghost/danger buttons, dark outline
  on the yellow accent button, accent outline around text
  fields while focused). Focus rings are never removed.
- **Disabled** elements mute (text → `MUTED`, surface → `PANEL`;
  accent → `#57500F`/`#8A8A8A`), lose the hand cursor and never
  fire — including via `invoke()`.
- Buttons are **≥ 36px tall** with ≥ 16px horizontal padding;
  Return/Space activate a focused button.

## Liquid Glass (v0.18)

The 2026 material pass (Apple's iOS 26 "Liquid Glass" is the
reference): translucent surfaces, a rim of light along the top
edge, and depth from shadow instead of flat fills. The brand
palette above is unchanged — glass is a *material* applied to
the existing tokens, not a new colour scheme.

### Web — real glass (both dashboards)

- **Ambient backdrop**: the page background is layered —
  `radial-gradient(600px 400px at 15% -5%, rgba(245,216,0,.07),
  transparent 60%)`, a second cool glow at the opposite corner,
  over the solid `BG` base, `background-attachment: fixed`. It
  stays subtle on purpose: the data is the hero, the glass just
  needs something to refract.
- **Glass surfaces** (cards, panels, stat tiles, sidebar,
  top bars, settings panels): `background:
  rgba(255,255,255,.045)` (`--glass`), `-webkit-backdrop-filter`
  + `backdrop-filter: blur(16px) saturate(150%)`, `border: 1px
  solid rgba(255,255,255,.09)`, `box-shadow: inset 0 1px 0
  rgba(255,255,255,.08), 0 8px 32px rgba(0,0,0,.35)` — the
  inset top highlight is the rim light, the drop shadow is the
  depth.
- **Lighter glass** (inputs, selects, ghost/secondary buttons,
  icon chips, the agents box): `rgba(255,255,255,.05)` with
  `blur(10px)` and border `rgba(255,255,255,.10)`.
- **Accent CTA stays solid** `#F5D800` — glass is for surfaces,
  never for the primary action (contrast + affordance).
- **Tables stay readable**: glass applies to the table's card
  container only; row backgrounds are transparent, the header
  row is `rgba(255,255,255,.03)`.
- **Fallbacks**: `@supports not ((backdrop-filter: blur(1px))
  or (-webkit-backdrop-filter: blur(1px)))` and
  `@media (prefers-reduced-transparency: reduce)` re-point
  every `--glass*` token at the pre-v0.18 solid colours
  (`#15151A` / `#1C1C22` / `#232329` / `#101014`) and switch
  the blur tokens to `none` — same layout, flat material.

### Desktop — simulated glass (no blur, stated plainly)

Tk cannot blur whatever sits behind a window, so the desktop
apps **simulate** the material and do not pretend otherwise:

| Token | Value | Use |
|---|---|---|
| `PANEL_GLASS` | `#191920` | card fill (glass tint) |
| `GLASS_BORDER` | `#34343E` | card + ghost-button outline |
| `RIM_LIGHT` | `#3D3D4A` | 1px rim light, top inner edge |
| `GHOST_FILL` | `#22222B` | ghost button fill |
| `ENTRY_FILL` | `#1E1E26` | entry fill |
| `ENTRY_BORDER` | `#30303C` | entry outline (focus → `ACCENT`) |

`RoundedCard` and ghost-variant `RoundedButton`s draw the rim
light as a real canvas line (top arc + straight, inset 1px,
`RIM_LIGHT`) on every redraw, so resizes never double it. Pills
stay solid (status reads as material, not glass), the accent
button stays solid yellow, and the Treeview/detail text keep
the solid `PANEL`/`PANEL2` surfaces inside their glass cards.

### Contrast

Glass tints are only ever layered over the near-black base,
and text always sits on the resulting effectively-solid dark
surface: `TEXT` on a glass card composites to ≈14:1 and
`MUTED` to ≈7:1 — the same ratios as the solid panels they
replaced, comfortably above the 4.5:1 floor.

## Status pills

Pills are fully round with bold small text on a solid tone
fill: `ok` green, `warn` amber, `bad` red, `dim` panel2/muted —
text on ok/warn/bad fills is `ACCENT_TEXT` for contrast.
