# Quick Image Search for Anki

An Anki add-on that adds a **Search Images** button to the editor toolbar. Clicking it opens an image search for the text in a configurable note field — making it easy to find images for your flashcards without leaving Anki.

## Features

- Toolbar button in the Browse window editor
- Searches the configured note field (falls back to the first field if not found)
- Supports 12 Google country domains plus a custom domain option
- Simple settings dialog via **Tools → Add-ons → Config**

## Installation

### From AnkiWeb
1. In Anki, go to **Tools → Add-ons → Get Add-ons...**
2. Enter code **183246496**
3. Restart Anki

### From `.ankiaddon` file
1. Download `quick_image_search.ankiaddon`
2. In Anki, go to **Tools → Add-ons → Install from file...**
3. Select the downloaded file and restart Anki

## Configuration

Go to **Tools → Add-ons → Quick Image Search for Anki → Config**

| Setting | Default | Description |
|---|---|---|
| `field_name` | `Front` | Which note field to search |
| `google_domain` | `google.com` | Which image search domain to use |

Supported domains include google.com, google.co.uk, google.de, google.fr, google.co.jp, and more — or enter a custom domain.

## Requirements

- Anki 2.1.50 or later
- Tested on Anki 25.02.5 (Python 3.9, Qt 6.6.2, macOS arm64)

## License

MIT

## Show Your Support
    
[![Buy me a coffee](https://media.giphy.com/media/o7RZbs4KAA6tvM4H6j/giphy.gif)](https://buymeacoffee.com/bappelt)