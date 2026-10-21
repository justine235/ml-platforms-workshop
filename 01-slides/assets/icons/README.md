# Icon build

Generated icon set for the ML platforms deck.

## Regenerate

1. Pick a scratch folder outside `assets\icons`, set the `ICON_BUILD_DIR` environment variable to it, and install the dependencies there if they are missing:
   - `npm install --prefix "%ICON_BUILD_DIR%" sharp lucide-static @fabric-msft/svg-icons @primer/octicons jszip pngjs --no-audit --no-fund`
2. From this folder, run:
   - `node scripts\build_icons.mjs`

The build is family-safe: it renders into a temporary folder under `assets\icons`, publishes each family only after that family is complete, retries downloads, and leaves previously published families untouched if a later family fails.

The script writes:

- `lucide\*.svg` and `png\<color>\*.png`
- `microsoft\svg\*.svg` and `microsoft\png\*.png`
- `tiles\*.png`
- `catalog.json`, `PROVENANCE.md`, `README.md`, `STATUS.md`, `contact-sheet.png`

## Naming rules

- File names are stable slugs used directly by slide authors (`add_icon(..., "name")`).
- Lucide compatibility aliases keep the requested old deck names even when Lucide renamed the upstream glyph.
- Microsoft assets stay colourless and unmodified; only placement/scaling changes when rasterising PNGs.
- Text tiles are neutral labels, not vendor logos.

## How the deck loads icons

- `deck_core.py::icon_file()` scans every PNG under `assets\icons`.
- A parent folder named `amber`, `azure`, `ink`, `muted`, `success`, or `white` marks a Lucide colour variant.
- Lookup order is `(name, color)`, `(name, none)`, `(name, azure)`, then any remaining match.

## Sources and package versions

- Lucide generic icons: `lucide-static 1.55.0` (ISC)
- Microsoft Fabric icons: `@fabric-msft/svg-icons 11.0.0` (MIT package; Microsoft Learn usage terms also reviewed)
- GitHub mark: `@primer/octicons 19.40.0` (MIT)
- Azure, Entra, VS Code: official Microsoft downloads / brand pages referenced in `PROVENANCE.md`

## Missing items

- `activator`: No current official Activator icon was found in the Microsoft Fabric Learn download or the official @fabric-msft/svg-icons package. Nearest alternative: No official alternative shipped in the approved Microsoft sources; use a neutral text tile only if a slide must label Activator explicitly.
- `azure-bicep`: No official Azure/Bicep product icon was offered in the Azure architecture pack or the other approved Microsoft icon sources checked for this task. Nearest alternative: No official Microsoft product icon is published in the approved sources; use the neutral bicep text tile when the concept must appear on a slide.

## Catalog counts

- Lucide: 93
- Microsoft / official vendor: 28
- Text tiles: 13

