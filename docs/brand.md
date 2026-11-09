# BeeSky brand

Source of truth: https://api.beeskybase.com (system name "BeeskyBase",
logo path /beesky-logo.svg). The logo served there is byte-identical to
the master logo file kept in the ASIC project assets (chevron-V mark).

## Colors (sampled from the logo artwork)

| Role      | Hex       | Notes                                  |
|-----------|-----------|----------------------------------------|
| Primary   | `#F5D800` | BeeSky yellow — logo mark, highlights  |
| Ink       | `#000000` | Black — logo background/outline, text  |
| Surface   | `#FFFFFF` | White — backgrounds                    |

Rule of thumb: black surfaces with #F5D800 accents read as BeeSky;
avoid other saturated colors competing with the yellow. Status colors
(OK/warn/error) may be used functionally in tooling UIs, kept muted.

## Logo files (ASIC project, not in this repo)

- `~/workspace/asic-os-s19pro/assets/logo-user.jpg` — master (2051x2301)
- `~/workspace/asic-os-s19pro/assets/beesky-brand/beesky-logo.svg` —
  copy as served by api.beeskybase.com (SVG wrapper, embedded JPEG)
- `~/workspace/asic-os-s19pro/assets/logo-transparent.png` — transparent cut
