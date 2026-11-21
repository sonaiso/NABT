"""Finite style/work signatures of the deposited NABT table."""
from collections import defaultdict
from hashlib import sha256
import re

from nabt.governors import installed_table
from .catalog import ROOT

STYLE_FILE = "vendor/mashru/Jisr/AwamilUslub.lean"
STYLE_SHA256 = "d32bc4c4c63b45c1a537595f2aee384c1c42c7b023c1e1b8929e8ea65b1f9ae6"


def profiles():
    raw = (ROOT / STYLE_FILE).read_bytes()
    if sha256(raw).hexdigest() != STYLE_SHA256:
        raise ValueError("Governor style source differs from the pinned table")
    styles = re.findall(r'^  \("([^"]+)", "([^"]+)"\)', raw.decode("utf-8"), re.MULTILINE)
    table = installed_table()
    members = defaultdict(list)
    rows = {}
    for entry, (label, style) in zip(table.entries, styles, strict=True):
        if label != entry.label:
            raise ValueError("Governor and style labels differ at the same row")
        cls = table.classes[entry.class_code]
        signature = (cls.alternatives, cls.links, style, entry.implicit)
        members[signature].append(entry.row_id)
        rows[entry.row_id] = signature
    return rows, members


def describe(entry):
    rows, members = profiles()
    key = rows[entry.row_id]
    alternatives, links, style, implicit = key
    return {
        "schema": "nabt.governor-work-style-profile.v1",
        "representative_row": members[key][0],
        "member_rows": members[key],
        "source_label": entry.label,
        "same_label_rows": [r.row_id for r in installed_table().entries if r.label == entry.label],
        "table_style": style,
        "style_group": "إخبار" if style == "الخبر" else "إنشاء",
        "alternatives": [[list(eq) for eq in alt] for alt in alternatives],
        "equality_links": [list(link) for link in links],
        "implicit_governor": implicit,
        "style_source": {"path": STYLE_FILE, "sha256": STYLE_SHA256, "row": entry.row_id},
        "scope": "DEPOSITED_TABLE_ROW",
    }
