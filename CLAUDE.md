# Quick Image Search for Anki

## Overview
An Anki add-on that adds a "Search Images" button to the editor toolbar in the Browse window. Clicking it opens an image search for the text in a configurable note field, helping users quickly find images to add to their flashcards.

## Files
- `__init__.py` — main add-on code
- `search.svg` — magnifying glass / image icon for the toolbar button
- `config.json` — default configuration
- `build.py` — script to package the add-on
- `quick_image_search.ankiaddon` — installable package (zip of the above + manifest.json)

## Environment
- Anki version: 25.9.4 (bundled Python 3.13; earlier 25.x bundled 3.9)
- Target: `min_point_version` 50, so keep the code 3.9-compatible
- Platform: macOS 14.6.1 arm64
- Qt: 6.6.2 / PyQt 6.6.1

## Important Python Notes
- The add-on targets Anki 2.1.50+, which may bundle Python 3.9, so **do not use `str | None` syntax** — use `Optional[str]` from `typing` instead
- `collection.anki21b` files are zstd-compressed SQLite databases

## How It Works
1. `gui_hooks.editor_did_init_buttons` — adds the toolbar button when the editor initializes
2. `editor.addButton()` — creates the button with the SVG icon
3. When clicked, reads the configured field from `editor.note`
4. URL-encodes the field text and opens an image search in the default browser
5. `mw.addonManager.setConfigAction()` — registers a custom Qt config dialog instead of raw JSON editing

## Configuration
Users access settings via **Tools → Add-ons → Quick Image Search for Anki → Config**

Settings:
- `field_name` — which note field to search (default: `"Front"`)
- `google_domain` — which Google domain to use (default: `"google.com"`)
- `shortcut` — keyboard shortcut for the toolbar button (default: `"Ctrl+Shift+1"`, empty string disables it)

The config dialog (`ConfigDialog` class) is a Qt `QDialog` with:
- A `QLineEdit` for the field name
- A `QComboBox` with common Google country domains
- A `QLineEdit` for custom domains (shown/hidden dynamically)
- A `QKeySequenceEdit` (plus a Clear button) for the shortcut

## Key Learnings / Gotchas
- **Do not read `mw.reviewer.card` on button click** — the reviewer loses card context when a button is clicked. Instead, capture card data at display time using `card_will_show` hook and store in a module-level variable.
- **`card_will_show` hook** receives the card object directly, making it reliable for capturing note data.
- **`.ankiaddon` format** is a zip file containing `__init__.py`, assets, and a `manifest.json`. Only `package` and `name` are strictly required; unknown keys validate but are silently discarded.
- **Add-ons have no semantic version.** Anki decides an update is available by comparing timestamps — `AddonMeta.is_latest()` is just `installed_at >= server_update_time`, where `installed_at` is the manifest's `mod`. `human_version` is never compared, so bumping it alone ships nothing. It is also *not* shown in the add-on manager — `name_for_addon_list()` renders only the name plus a disabled/incompatible suffix. Its single consumer is `addon_debug_info()` in `aqt/errors.py`, i.e. the add-on list in error reports. AnkiWeb overwrites `mod` with its own upload time, so the locally generated `mod` only matters for direct `.ankiaddon` installs.
- **`min_point_version` / `max_point_version`** use `int_version()` (`YYMMPP`, so 25.9.4 is `250904`); values <= 99 are the old `2.1.x` scheme. A *negative* `max_point_version` sets the maximum supported version — a positive one means "tested on" and is ignored.
- **`editor.addButton(keys=...)` alone is NOT enough for an editor shortcut.** It registers a `QShortcut` on `editor.widget`, but the editor is a QtWebEngine view: while the caret is in a field, Chromium accepts Qt's `ShortcutOverride` for editable content and the QShortcut never fires. The shortcut must *also* be installed as a `keydown` listener inside the editor page (`editor.web.eval`, capture phase on `document`) that calls `pycmd("<cmd>")`. `Editor.onBridgeCmd` dispatches unknown commands via `self._links[cmd]`, which `addButton` populates — so the JS path reuses the exact same handler, note-save wrapper included. See `install_web_shortcut`.
- **macOS modifier swap** — Qt's `ControlModifier` is the Command key on macOS and `MetaModifier` is the physical Control key; the DOM reports them unswapped, so `shortcut_to_dom_spec()` swaps `ctrl`/`meta` on darwin.
- **`QKeySequenceEdit` can tag a number-row key with the keypad modifier** — on macOS, pressing ⌘⇧1 in the dialog yields the portable text `Ctrl+Shift+Num+1`, and a `QKeySequence` carrying `Num+` never matches the top-row key. `normalize_shortcut()` strips the token on both save and read, so already-saved configs heal on load.
- **Match on `event.code`, not `event.key`** — with Shift held, `event.key` for `Shift+G` is `"G"` and for `Shift+,` is `"<"`, while `event.code` stays `KeyG` / `Comma`.
- **Shortcuts are bound at button-creation time** — `addButton(keys=...)` is only read when the editor initializes, so a changed shortcut applies to editor windows opened after saving. The web listener re-installs on every note load, so it picks up a change sooner.
- **`collection.anki21b`** is zstd-compressed and cannot be opened directly with sqlite3 — decompress first with the `zstandard` Python package.

## Packaging
To rebuild the `.ankiaddon`, run:
```
python3 build.py
```
This generates `quick_image_search.ankiaddon` with a fresh `mod` timestamp.

## Future Ideas
- Publish to AnkiWeb shared add-ons
- Change default `field_name` from "Front" to something smarter (auto-detect first field)
- Support searching multiple fields
- Add option to search a different image provider (e.g. Bing, DuckDuckGo)
