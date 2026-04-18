# Anki Google Image Search Add-on

## Overview
An Anki add-on that adds a "Search Images" button to the editor toolbar in the Browse window. Clicking it opens a Google Image search for the text in a configurable note field, helping users quickly find images to add to their flashcards.

## Files
- `__init__.py` — main add-on code
- `search.svg` — magnifying glass / image icon for the toolbar button
- `config.json` — default configuration
- `google_image_search.ankiaddon` — installable package (zip of the above + manifest.json)

## Environment
- Anki version: 25.02.5
- Python: 3.9.18 (bundled with Anki)
- Platform: macOS 14.6.1 arm64
- Qt: 6.6.2 / PyQt 6.6.1

## Important Python Notes
- Anki 25 bundles Python 3.9, so **do not use `str | None` syntax** — use `Optional[str]` from `typing` instead
- `collection.anki21b` files are zstd-compressed SQLite databases

## How It Works
1. `gui_hooks.editor_did_init_buttons` — adds the toolbar button when the editor initializes
2. `editor.addButton()` — creates the button with the SVG icon
3. When clicked, reads the configured field from `editor.note`
4. URL-encodes the field text and opens a Google Image search in the default browser
5. `mw.addonManager.setConfigAction()` — registers a custom Qt config dialog instead of raw JSON editing

## Configuration
Users access settings via **Tools → Add-ons → Google Image Search for Editor → Config**

Settings:
- `field_name` — which note field to search (default: `"Front"`)
- `google_domain` — which Google domain to use (default: `"google.com"`)

The config dialog (`ConfigDialog` class) is a Qt `QDialog` with:
- A `QLineEdit` for the field name
- A `QComboBox` with common Google country domains
- A `QLineEdit` for custom domains (shown/hidden dynamically)

## Key Learnings / Gotchas
- **Do not read `mw.reviewer.card` on button click** — the reviewer loses card context when a button is clicked. Instead, capture card data at display time using `card_will_show` hook and store in a module-level variable.
- **`card_will_show` hook** receives the card object directly, making it reliable for capturing note data.
- **`.ankiaddon` format** is a zip file containing `__init__.py`, assets, and a `manifest.json`. The manifest requires at minimum: `package`, `name`, `mod`, `min_point_version`.
- **`collection.anki21b`** is zstd-compressed and cannot be opened directly with sqlite3 — decompress first with the `zstandard` Python package.

## Packaging
To rebuild the `.ankiaddon`:
```python
import zipfile, json

manifest = {
    "package": "google_image_search",
    "name": "Google Image Search for Editor",
    "mod": 1709150409,
    "min_point_version": 50
}

with zipfile.ZipFile("google_image_search.ankiaddon", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write("__init__.py")
    zf.write("search.svg")
    zf.write("config.json")
    zf.writestr("manifest.json", json.dumps(manifest))
```

## Future Ideas
- Publish to AnkiWeb shared add-ons
- Change default `field_name` from "Front" to something smarter (auto-detect first field)
- Support searching multiple fields
- Add option to search a different image provider (e.g. Bing, DuckDuckGo)
