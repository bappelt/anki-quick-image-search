import zipfile
import json
import time

manifest = {
    "package": "quick_image_search",
    "name": "Quick Image Search for Anki",
    "mod": int(time.time()),
    "min_point_version": 50,
    "version": "1.0.0"
}

output = "quick_image_search.ankiaddon"

with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write("__init__.py")
    zf.write("search.svg")
    zf.write("config.json")
    zf.writestr("manifest.json", json.dumps(manifest))

print("Built %s" % output)