# Quick Image Search for Anki

An Anki add-on that adds a **Search Images** button to the editor toolbar. Clicking it opens an image search for the text in a configurable note field — making it easy to find images for your flashcards without leaving Anki.

## Features

- Toolbar button in the Browse window editor
- Searches the configured note field (falls back to the first field if not found)
- Supports 12 Google country domains plus a custom domain option
- Configurable keyboard shortcut (default `Ctrl+Shift+1`, shown as ⇧⌘1 on macOS)
- Simple settings dialog via **Tools → Add-ons → Config**

## Installation

### From AnkiWeb (recommended)
1. In Anki, go to **Tools → Add-ons → Get Add-ons...**
2. Enter code **183246496** ([AnkiWeb page](https://ankiweb.net/shared/info/183246496))
3. Restart Anki

AnkiWeb installs get updates through **Tools → Add-ons → Check for Updates**.

### From a `.ankiaddon` file
1. Download `quick_image_search-<version>.ankiaddon` from the [latest GitHub release](https://github.com/bappelt/anki-quick-image-search/releases/latest)
2. In Anki, go to **Tools → Add-ons → Install from file...**
3. Select the downloaded file and restart Anki

> **Install it only one way.** Anki treats a copy installed from a file as a separate add-on from the AnkiWeb one, so with both enabled you get two Search Images buttons and two copies of the shortcut. If you switch, delete the old copy in **Tools → Add-ons** first.

## Configuration

Go to **Tools → Add-ons → Quick Image Search for Anki → Config**

| Setting | Default | Description |
|---|---|---|
| `field_name` | `Front` | Which note field to search |
| `google_domain` | `google.com` | Which image search domain to use |
| `shortcut` | `Ctrl+Shift+1` | Keyboard shortcut for the button (leave empty to disable) |

Supported domains include google.com, google.co.uk, google.de, google.fr, google.co.jp, and more — or enter a custom domain.

## Requirements

- Anki 2.1.50 or later
- Tested on Anki 26.09.3

## License

MIT

## Show Your Support
    
[![Buy me a coffee](https://media.giphy.com/media/o7RZbs4KAA6tvM4H6j/giphy.gif)](https://buymeacoffee.com/bappelt)