import zipfile
import json
import time

manifest = {
    "package": "quick_image_search",
    "name": "Quick Image Search for Anki",
    "mod": int(time.time()),
    "min_point_version": 50,
    # Cosmetic only: Anki compares "mod" timestamps, never this string.
    # Note that AnkiWeb overwrites "mod" with its own upload time, so the
    # timestamp below only matters for direct .ankiaddon installs.
    "human_version": "1.1.0",
}

output = "quick_image_search.ankiaddon"

with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write("__init__.py")
    zf.write("search.svg")
    zf.write("config.json")
    zf.writestr("manifest.json", json.dumps(manifest))

print("Built %s" % output)