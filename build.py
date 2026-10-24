"""Package the add-on as dist/quick_image_search-<version>.ankiaddon.

    python3 build.py

Generates manifest.json at build time (so "mod" is always fresh) and zips it
with the files in FILES. Install the result via Anki's
Tools > Add-ons > Install from file...

The version comes from the VERSION file, the project's single source of
truth for it.
"""

import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / "VERSION").read_text().strip()
OUT = ROOT / "dist" / f"quick_image_search-{VERSION}.ankiaddon"

FILES = ["__init__.py", "config.json", "search.svg"]

manifest = {
    # Anki installs a file install into addons21/<package>/. AnkiWeb installs
    # use the add-on id (183246496) as the folder name instead.
    "package": "quick_image_search",
    "name": "Quick Image Search for Anki",
    # Anki offers an update when the server's time is newer than this, so it
    # must change on every build. AnkiWeb overwrites it with its upload time.
    "mod": int(time.time()),
    "min_point_version": 50,  # Anki 2.1.50
    # Cosmetic only: Anki never compares this; it appears in error reports.
    "human_version": VERSION,
    "homepage": "https://github.com/bappelt/anki-quick-image-search",
}

OUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for name in FILES:
        zf.write(ROOT / name, name)
    zf.writestr("manifest.json", json.dumps(manifest, indent=4))

print("Built %s" % OUT.relative_to(ROOT))
