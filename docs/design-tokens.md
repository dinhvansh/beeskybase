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
| `PANEL` | `#15151A` | card surface |
| `PANEL2` | `#1C1C22` | inset fields, hover surfaces |
| `BORDER` | `#26262E` | hairline borders |
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

## Status pills

Pills are fully round with bold small text on a solid tone
fill: `ok` green, `warn` amber, `bad` red, `dim` panel2/muted —
text on ok/warn/bad fills is `ACCENT_TEXT` for contrast.
