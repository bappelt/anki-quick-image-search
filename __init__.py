"""
Quick Image Search for Anki
============================
Adds a "Search Images" button to the editor toolbar (in the Browse
window). Clicking it opens an image search for the text in a
configurable field of the current note.

Configuration:
  In Anki, go to Tools -> Add-ons -> select this add-on -> Config
  Or use the form dialog that appears.

Installation:
  1. In Anki, go to Tools -> Add-ons -> Open Add-ons Folder
  2. Create a new folder called "google_image_search"
  3. Copy this file into that folder as __init__.py
  4. Restart Anki
"""

import os
import re
import urllib.parse
import webbrowser
from typing import Optional

from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
)
from aqt.utils import tooltip


# --- Config ---

GOOGLE_DOMAINS = [
    ("Ukrainian - google.com.ua", "google.com.ua"),
    ("English (US) - google.com", "google.com"),
    ("English (UK) - google.co.uk", "google.co.uk"),
    ("Spanish - google.es", "google.es"),
    ("French - google.fr", "google.fr"),
    ("German - google.de", "google.de"),
    ("Italian - google.it", "google.it"),
    ("Portuguese - google.pt", "google.pt"),
    ("Polish - google.pl", "google.pl"),
    ("Japanese - google.co.jp", "google.co.jp"),
    ("Korean - google.co.kr", "google.co.kr"),
    ("Chinese - google.com.cn", "google.com.cn"),
]


def get_config():
    """Load add-on config with defaults."""
    conf = mw.addonManager.getConfig(__name__)
    if conf is None:
        conf = {}
    defaults = {
        "field_name": "Front",
        "google_domain": "google.com",
    }
    for key, val in defaults.items():
        if key not in conf:
            conf[key] = val
    return conf


def save_config(conf):
    """Save add-on config."""
    mw.addonManager.writeConfig(__name__, conf)


# --- Config Dialog ---

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Google Image Search - Settings")
        self.setMinimumWidth(400)

        conf = get_config()

        layout = QVBoxLayout()

        # Description
        desc = QLabel(
            "Configure which note field to search and which\n"
            "Google domain to use for image searches."
        )
        layout.addWidget(desc)

        # Form
        form = QFormLayout()

        self.field_input = QLineEdit()
        self.field_input.setText(conf["field_name"])
        self.field_input.setPlaceholderText("e.g. Ukrainian, Spanish, Front")
        form.addRow("Field name:", self.field_input)

        self.domain_combo = QComboBox()
        current_domain = conf["google_domain"]
        selected_index = 0
        for i, (label, domain) in enumerate(GOOGLE_DOMAINS):
            self.domain_combo.addItem(label, domain)
            if domain == current_domain:
                selected_index = i

        # Add "Custom" option
        self.domain_combo.addItem("Custom...", "custom")

        # Check if current domain is not in the predefined list
        known_domains = [d for _, d in GOOGLE_DOMAINS]
        if current_domain not in known_domains:
            selected_index = self.domain_combo.count() - 1

        self.domain_combo.setCurrentIndex(selected_index)

        form.addRow("Google domain:", self.domain_combo)

        self.custom_domain_input = QLineEdit()
        self.custom_domain_input.setPlaceholderText("e.g. google.com.br")
        if current_domain not in known_domains:
            self.custom_domain_input.setText(current_domain)
        self.custom_domain_input.setVisible(
            self.domain_combo.currentData() == "custom"
        )
        form.addRow("Custom domain:", self.custom_domain_input)

        self.domain_combo.currentIndexChanged.connect(self._on_domain_changed)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _on_domain_changed(self, index):
        is_custom = self.domain_combo.currentData() == "custom"
        self.custom_domain_input.setVisible(is_custom)

    def get_values(self):
        field_name = self.field_input.text().strip()
        if self.domain_combo.currentData() == "custom":
            domain = self.custom_domain_input.text().strip()
        else:
            domain = self.domain_combo.currentData()
        return field_name, domain


def on_config():
    """Show the config dialog."""
    dlg = ConfigDialog(mw)
    if dlg.exec():
        field_name, domain = dlg.get_values()
        if field_name and domain:
            conf = get_config()
            conf["field_name"] = field_name
            conf["google_domain"] = domain
            save_config(conf)
            tooltip("Settings saved. Field: %s, Domain: %s" % (field_name, domain))


# --- Core Functions ---

def strip_html(text):
    # type: (str) -> str
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    return text.strip()


def get_search_text(editor):
    # type: (Editor) -> Optional[str]
    """Get the text from the configured field of the current note,
    falling back to the first field if not found."""
    note = editor.note
    if not note or not note.fields:
        return None

    conf = get_config()
    field_name = conf["field_name"]

    field_names = [f["name"] for f in note.model()["flds"]]
    if field_name in field_names:
        raw = note[field_name]
    else:
        raw = note.fields[0]

    return strip_html(raw)


def on_search_images(editor):
    # type: (Editor) -> None
    """Open a Google Image search for the current note's text."""
    text = get_search_text(editor)
    if not text:
        tooltip("No card text found.")
        return

    conf = get_config()
    domain = conf["google_domain"]

    params = urllib.parse.urlencode({"tbm": "isch", "q": text})
    url = "https://www.%s/search?%s" % (domain, params)
    webbrowser.open(url)
    tooltip("Searching images for: %s" % text)


def add_editor_button(buttons, editor):
    # type: (list, Editor) -> None
    """Add the Search Images button to the editor toolbar."""
    icon = os.path.join(os.path.dirname(__file__), "search.svg")

    conf = get_config()
    domain = conf["google_domain"]
    tip_text = "Search Google Images (%s)" % domain

    if os.path.exists(icon):
        btn = editor.addButton(
            icon=icon,
            cmd="google_image_search",
            func=on_search_images,
            tip=tip_text,
            label="",
        )
    else:
        btn = editor.addButton(
            icon=None,
            cmd="google_image_search",
            func=on_search_images,
            tip=tip_text,
            label="Search Images",
        )

    buttons.append(btn)


# --- Setup ---

gui_hooks.editor_did_init_buttons.append(add_editor_button)

# Register custom config dialog so it opens instead of raw JSON
mw.addonManager.setConfigAction(__name__, on_config)
