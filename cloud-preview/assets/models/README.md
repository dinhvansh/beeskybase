# Miner model assets

Converted from the two archives supplied by the user:

- `s21-antminer-s21-hydro-bitcoin.zip` → `s21-hydro.glb` (water cooled)
- `ant-miner-s19-pro.zip` → `s19-pro-air.glb` (air cooled)

The archives did not include license metadata. No ownership or redistribution license is asserted here.

`tools/prepare_miner_models.py` exports static meshes with simplified geometry/materials and textures capped at 1024 pixels. Sources and portable Blender stay in ignored `work/`; they are not shipped. Run Blender with `--background --disable-autoexec --python tools/prepare_miner_models.py` from the repository root after extracting inputs into the paths documented in that script.

Both generated GLBs pass Khronos glTF Validator with zero errors and warnings. See `model-stats.json` for sizes and triangle counts.

The hydro studio backdrop is excluded, the front is oriented toward the rack aisle, and mesh normals/triangulation are repaired. Geometry budgets were increased to preserve fan grilles and chassis silhouettes.
# Optimized web models

The `*-fast.glb` files are generated from the original GLBs, which are retained.
They use Meshopt geometry compression, simplified geometry and WebP textures.
Three.js consumers must configure `MeshoptDecoder`; the shared loader is
`cloud-preview/rack3d/optimized-models.js`.

Rebuild from the repository root:

```powershell
npm ci --prefix cloud-preview/rack3d
npm run optimize:models --prefix cloud-preview/rack3d
```

`optimized-stats.json` records the actual output sizes and triangle counts.
The combined download is 1,402,916 bytes, compared with 10,733,092 bytes for
the originals. Authentication keeps a small rendered poster visible until
the actual scene and shaders are ready, and keeps the same scene between forms.

