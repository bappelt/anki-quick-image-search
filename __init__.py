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
  1. Download quick_image_search.ankiaddon (run build.py to generate it)
  2. In Anki, go to Tools -> Add-ons -> Install from file...
  3. Select the downloaded file and restart Anki
"""

import json
import os
import re
import sys
import time
import urllib.parse
import webbrowser
from typing import Optional

from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequence,
    QKeySequenceEdit,
    Qt,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QVBoxLayout,
)
from aqt.utils import tooltip


# --- Config ---

DEFAULT_SHORTCUT = "Ctrl+Shift+1"

# Qt's portable-text token for the keypad modifier. QKeySequenceEdit can
# tag a plain number-row press with it (it does on macOS), and the
# resulting sequence then never matches that key. Strip it.
KEYPAD_TOKEN = "Num+"


def normalize_shortcut(shortcut):
    # type: (Optional[str]) -> str
    """Drop the keypad modifier and re-render as portable text."""
    if not shortcut:
        return ""
    seq = QKeySequence(shortcut.replace(KEYPAD_TOKEN, ""))
    if seq.count() == 0:
        return ""
    return seq.toString(QKeySequence.SequenceFormat.PortableText)

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
        "shortcut": DEFAULT_SHORTCUT,
    }
    for key, val in defaults.items():
        if key not in conf:
            conf[key] = val
    conf["shortcut"] = normalize_shortcut(conf["shortcut"])
    return conf


def save_config(conf):
    """Save add-on config."""
    mw.addonManager.writeConfig(__name__, conf)


# --- Config Dialog ---

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Image Search - Settings")
        self.setMinimumWidth(400)

        conf = get_config()

        layout = QVBoxLayout()

        # Description
        desc = QLabel(
            "Configure which note field to search, which Google domain\n"
            "to use, and the keyboard shortcut for the toolbar button."
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

        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setKeySequence(QKeySequence(conf["shortcut"]))
        # Qt 6.5+ only; older builds capture multi-key sequences, which
        # get_values() truncates to the first one anyway.
        if hasattr(self.shortcut_edit, "setMaximumSequenceLength"):
            self.shortcut_edit.setMaximumSequenceLength(1)

        clear_btn = QPushButton("Clear")
        clear_btn.setToolTip("Remove the shortcut")
        clear_btn.clicked.connect(self.shortcut_edit.clear)

        shortcut_row = QHBoxLayout()
        shortcut_row.addWidget(self.shortcut_edit)
        shortcut_row.addWidget(clear_btn)
        form.addRow("Shortcut:", shortcut_row)

        layout.addLayout(form)

        hint = QLabel(
            "Leave the shortcut empty to disable it. Shortcut changes apply\n"
            "to editor windows opened after saving."
        )
        layout.addWidget(hint)

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

        seq = self.shortcut_edit.keySequence()
        if seq.count() > 1:
            # Keep only the first key of a multi-key sequence.
            seq = QKeySequence(seq[0])
        shortcut = normalize_shortcut(
            seq.toString(QKeySequence.SequenceFormat.PortableText)
        )

        return field_name, domain, shortcut


def on_config():
    """Show the config dialog."""
    dlg = ConfigDialog(mw)
    if dlg.exec():
        field_name, domain, shortcut = dlg.get_values()
        if field_name and domain:
            conf = get_config()
            conf["field_name"] = field_name
            conf["google_domain"] = domain
            conf["shortcut"] = shortcut
            save_config(conf)
            tooltip(
                "Settings saved. Field: %s, Domain: %s, Shortcut: %s"
                % (field_name, domain, shortcut or "none")
            )


# --- Shortcut plumbing ---

# Anki's editor is a QtWebEngine view. While the caret is inside a field,
# Chromium claims the key event (it accepts Qt's ShortcutOverride for
# editable content), so the QShortcut that editor.addButton(keys=...)
# registers never fires. The shortcut is therefore also installed as a
# keydown listener inside the editor page, which calls back into the same
# bridge command the toolbar button uses.

EDITOR_CMD = "google_image_search"

# Qt key name -> DOM KeyboardEvent.code, for keys that aren't a plain
# letter, digit or function key.
DOM_CODES = {
    "Space": "Space",
    "Return": "Enter",
    "Enter": "NumpadEnter",
    "Backspace": "Backspace",
    "Tab": "Tab",
    "Esc": "Escape",
    "Ins": "Insert",
    "Del": "Delete",
    "Home": "Home",
    "End": "End",
    "PgUp": "PageUp",
    "PgDown": "PageDown",
    "Left": "ArrowLeft",
    "Right": "ArrowRight",
    "Up": "ArrowUp",
    "Down": "ArrowDown",
    ",": "Comma",
    ".": "Period",
    ";": "Semicolon",
    "'": "Quote",
    "[": "BracketLeft",
    "]": "BracketRight",
    "\\": "Backslash",
    "/": "Slash",
    "-": "Minus",
    "=": "Equal",
    "`": "Backquote",
}


def _enum_value(val):
    """PyQt enums expose .value; older bindings are plain ints."""
    return val.value if hasattr(val, "value") else int(val)


def shortcut_to_dom_spec(shortcut):
    # type: (str) -> Optional[dict]
    """Translate a Qt key sequence into a DOM KeyboardEvent matcher.

    Returns None if the sequence is empty or uses a key we can't map."""
    if not shortcut:
        return None

    seq = QKeySequence(shortcut)
    if seq.count() == 0:
        return None

    combo = seq[0]
    # Qt 5 indexes a sequence as plain ints, Qt 6 as QKeyCombination.
    if hasattr(combo, "key"):
        key = _enum_value(combo.key())
        mods = _enum_value(combo.keyboardModifiers())
    else:
        key = int(combo) & ~int(Qt.KeyboardModifier.KeyboardModifierMask)
        mods = int(combo) & int(Qt.KeyboardModifier.KeyboardModifierMask)

    code = None
    key_a = _enum_value(Qt.Key.Key_A)
    key_0 = _enum_value(Qt.Key.Key_0)
    key_f1 = _enum_value(Qt.Key.Key_F1)
    if key_a <= key <= _enum_value(Qt.Key.Key_Z):
        code = "Key" + chr(key)
    elif key_0 <= key <= _enum_value(Qt.Key.Key_9):
        code = "Digit" + chr(key)
    elif key_f1 <= key <= _enum_value(Qt.Key.Key_F24):
        code = "F%d" % (key - key_f1 + 1)
    else:
        name = QKeySequence(key).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        code = DOM_CODES.get(name)

    if not code:
        return None

    ctrl = bool(mods & _enum_value(Qt.KeyboardModifier.ControlModifier))
    meta = bool(mods & _enum_value(Qt.KeyboardModifier.MetaModifier))

    # On macOS Qt swaps the two: ControlModifier is Command, MetaModifier
    # is the physical Control key. The DOM reports them unswapped.
    if sys.platform == "darwin":
        ctrl, meta = meta, ctrl

    return {
        "code": code,
        "ctrl": ctrl,
        "meta": meta,
        "shift": bool(mods & _enum_value(Qt.KeyboardModifier.ShiftModifier)),
        "alt": bool(mods & _enum_value(Qt.KeyboardModifier.AltModifier)),
    }


# Guards against the Qt shortcut and the DOM listener both firing for a
# single keypress.
_last_activation = [0.0]


def _debounced(func):
    def wrapper(editor):
        now = time.time()
        if now - _last_activation[0] < 0.25:
            return
        _last_activation[0] = now
        return func(editor)

    return wrapper


def install_web_shortcut(editor):
    # type: (Editor) -> None
    """Install the configured shortcut as a keydown listener in the
    editor page, so it also works while a field has focus."""
    spec = shortcut_to_dom_spec(get_config()["shortcut"])

    editor.web.eval(
        """
(() => {
    const slot = "_quickImageSearchShortcut";
    if (window[slot]) {
        document.removeEventListener("keydown", window[slot], true);
        window[slot] = null;
    }
    const spec = %s;
    if (!spec) {
        return;
    }
    const handler = (event) => {
        if (event.code !== spec.code) return;
        if (event.ctrlKey !== spec.ctrl) return;
        if (event.metaKey !== spec.meta) return;
        if (event.shiftKey !== spec.shift) return;
        if (event.altKey !== spec.alt) return;
        event.preventDefault();
        event.stopPropagation();
        pycmd("%s");
    };
    window[slot] = handler;
    document.addEventListener("keydown", handler, true);
})();
"""
        % (json.dumps(spec), EDITOR_CMD)
    )


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
    # An empty shortcut means "no shortcut"; addButton treats it as unset.
    keys = conf["shortcut"] or None

    tip_text = "Search Google Images (%s)" % domain
    if keys:
        tip_text += " - %s" % QKeySequence(keys).toString(
            QKeySequence.SequenceFormat.NativeText
        )

    func = _debounced(on_search_images)

    if os.path.exists(icon):
        btn = editor.addButton(
            icon=icon,
            cmd=EDITOR_CMD,
            func=func,
            tip=tip_text,
            label="",
            keys=keys,
        )
    else:
        btn = editor.addButton(
            icon=None,
            cmd=EDITOR_CMD,
            func=func,
            tip=tip_text,
            label="Search Images",
            keys=keys,
        )

    buttons.append(btn)


# --- Setup ---

gui_hooks.editor_did_init_buttons.append(add_editor_button)

# The Qt shortcut registered above only fires when the caret is outside a
# field, so mirror it inside the editor page once a note is loaded.
gui_hooks.editor_did_load_note.append(install_web_shortcut)

# Register custom config dialog so it opens instead of raw JSON
mw.addonManager.setConfigAction(__name__, on_config)
