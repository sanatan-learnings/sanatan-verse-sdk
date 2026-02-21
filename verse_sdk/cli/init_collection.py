#!/usr/bin/env python3
"""
Scaffold a collection index page (index.html) from _data/collections.yml
and the existing verse files in _verses/{collection}/.

The generated page includes:
- Hero section with title image
- puranic-legend-compact notice
- Verse grid with has-puranic-context and puranic-badge on every card
- Section headers auto-detected from verse file prefixes (doha/chaupai/pada/etc.)

Usage:
    verse-init-collection --collection hanuman-chalisa
    verse-init-collection --collection bajrang-baan --overwrite
    verse-init-collection --all
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# ---------------------------------------------------------------------------
# Section label + icon registry
# ---------------------------------------------------------------------------

_SECTION_LABELS: Dict[str, Dict] = {
    "chaupai":      {"en": "Chaupai",       "hi": "चौपाई",          "icon": "📿"},
    "doha":         {"en": "Doha",          "hi": "दोहा",           "icon": "🪷"},
    "pada":         {"en": "Pada",          "hi": "पद",             "icon": "🎵"},
    "shloka":       {"en": "Shloka",        "hi": "श्लोक",          "icon": "📖"},
    "stanza":       {"en": "Stanza",        "hi": "स्तुति",          "icon": "📜"},
    "verse":        {"en": "Verse",         "hi": "पद",             "icon": "📖"},
    "mangalacharan":{"en": "Mangalacharan", "hi": "मंगलाचरण",       "icon": "🙏"},
    "vithi":        {"en": "Vithi",         "hi": "वीथी",           "icon": "🎋"},
    "stuti":        {"en": "Stuti",         "hi": "स्तुति",          "icon": "✨"},
}

_SUFFIX_QUALIFIERS: Dict[str, Dict] = {
    "opening":    {"en": "Opening",    "hi": "प्रारंभिक"},
    "closing":    {"en": "Closing",    "hi": "समापन"},
    "invocation": {"en": "Invocation", "hi": "आवाहन"},
    "final":      {"en": "Final",      "hi": "अंतिम"},
}


def _section_label(prefix: str, qualifier: Optional[str] = None) -> Tuple[str, str, str]:
    """Return (icon, en_label, hi_label) for a section type."""
    info = _SECTION_LABELS.get(prefix, {
        "en": prefix.replace("-", " ").title(),
        "hi": prefix.replace("-", " ").title(),
        "icon": "📿",
    })
    icon = info["icon"]
    en = info["en"]
    hi = info["hi"]
    if qualifier:
        qual = _SUFFIX_QUALIFIERS.get(qualifier, {
            "en": qualifier.replace("-", " ").title(),
            "hi": qualifier.replace("-", " ").title(),
        })
        en = f"{qual['en']} {en}"
        hi = f"{qual['hi']} {hi}"
    return icon, en, hi


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

def detect_sections(verses_dir: Path, sequence: Optional[List[str]] = None) -> List[Dict]:
    """
    Scan verse files and group consecutive same-prefix runs.

    Returns a list of dicts:
        { prefix, verse_ids, is_loop, qualifier }

    is_loop=True  → all verses are numbered (01, 02 ...) and there are >3 of them
    qualifier     → named suffix for single-verse sections (opening, closing, etc.)

    sequence: optional ordered list of verse IDs (from canonical YAML _meta.sequence).
    When provided, verse IDs are ordered by their position in sequence rather than
    alphabetically — this preserves natural order (e.g. doha-opening, chaupai-01..N,
    doha-closing) rather than collapsing them alphabetically.
    """
    if not verses_dir.exists():
        return []

    all_stems = {f.stem for f in verses_dir.glob("*.md")}

    if sequence:
        # Use sequence order; append any files not in sequence at the end
        ordered = [vid for vid in sequence if vid in all_stems]
        ordered += sorted(all_stems - set(ordered))
        verse_ids = ordered
    else:
        verse_ids = sorted(all_stems)

    def _prefix(vid: str) -> str:
        parts = vid.rsplit("-", 1)
        return parts[0] if len(parts) == 2 else vid

    # Group consecutive same-prefix runs
    sections: List[Dict] = []
    for vid in verse_ids:
        p = _prefix(vid)
        if sections and sections[-1]["prefix"] == p:
            sections[-1]["verse_ids"].append(vid)
        else:
            sections.append({"prefix": p, "verse_ids": [vid]})

    for section in sections:
        vids = section["verse_ids"]
        all_numbered = all(vid.rsplit("-", 1)[-1].isdigit() for vid in vids)
        section["is_loop"] = all_numbered and len(vids) > 3

        # Qualifier for single named verses (doha-opening → qualifier "opening")
        if len(vids) == 1:
            suffix = vids[0].rsplit("-", 1)[-1] if "-" in vids[0] else ""
            section["qualifier"] = suffix if not suffix.isdigit() else None
        else:
            section["qualifier"] = None

    return sections


# ---------------------------------------------------------------------------
# Template builders
# ---------------------------------------------------------------------------

def _loop_section(prefix: str, collection_key: str, icon: str, en: str, hi: str) -> str:
    num_en = f"{en} {{{{ verse.section_verse_number }}}}"
    num_hi = f"{hi} {{{{ verse.section_verse_number }}}}"
    return (
        f"\n"
        f"    {{% assign {prefix}_verses = site.verses"
        f" | where: \"collection_key\", \"{collection_key}\""
        f" | where_exp: \"item\", \"item.url contains '{prefix}-'\""
        f" | sort: \"section_verse_number\" %}}\n"
        f"    {{% assign {prefix}_count = {prefix}_verses | size %}}\n"
        f"    <h3>{icon}"
        f" <span data-lang=\"en\">{en} ({{% raw %}}{{{{ {prefix}_count }}}}{{% endraw %}} Verses)</span>"
        f"<span data-lang=\"hi\">{hi} ({{% raw %}}{{{{ {prefix}_count }}}}{{% endraw %}} पद)</span>"
        f"</h3>\n"
        f"    <div class=\"verse-grid\">\n"
        f"        {{% for verse in {prefix}_verses %}}\n"
        f"        {_card_block('verse', num_en, num_hi)}\n"
        f"        {{% endfor %}}\n"
        f"    </div>"
    )


def _individual_section(verse_ids: List[str], collection_key: str, icon: str, en: str, hi: str) -> str:
    count = len(verse_ids)
    count_en = f"{count} {'Verse' if count == 1 else 'Verses'}"
    count_hi = f"{count} पद"

    cards = []
    for vid in verse_ids:
        var = vid.replace("-", "_")
        suffix = vid.rsplit("-", 1)[-1] if "-" in vid else ""
        if suffix.isdigit():
            num = int(suffix)
            num_en = f"{en} {num}"
            num_hi = f"{hi} {num}"
        else:
            q = _SUFFIX_QUALIFIERS.get(suffix, {
                "en": suffix.replace("-", " ").title(),
                "hi": suffix.replace("-", " ").title(),
            })
            num_en = f"{q['en']} {en}"
            num_hi = f"{q['hi']} {hi}"

        card = (
            f"        {{% assign {var} = site.verses"
            f" | where: \"collection_key\", \"{collection_key}\""
            f" | where_exp: \"item\", \"item.url contains '{vid}'\" | first %}}\n"
            f"        {{% if {var} %}}\n"
            f"        {_card_block(var, num_en, num_hi)}\n"
            f"        {{% endif %}}"
        )
        cards.append(card)

    return (
        f"\n"
        f"    <h3>{icon}"
        f" <span data-lang=\"en\">{en} ({count_en})</span>"
        f"<span data-lang=\"hi\">{hi} ({count_hi})</span>"
        f"</h3>\n"
        f"    <div class=\"verse-grid\">\n"
        + "\n".join(cards) + "\n"
        "    </div>"
    )


def _card_block(var: str, num_en: str, num_hi: str) -> str:
    """Liquid HTML for a verse card. var is the Liquid variable name."""
    return (
        f"<a href=\"{{{{ {var}.url | relative_url }}}}\""
        f" class=\"verse-card{{% if {var}.puranic_context %}} has-puranic-context{{% endif %}}\">\n"
        f"            {{% if {var}.image %}}\n"
        f"            <div class=\"card-image\">\n"
        f"                <img src=\"{{{{ {var}.image | relative_url }}}}\" alt=\"{{{{ {var}.title_en }}}}\" loading=\"lazy\">\n"
        f"            </div>\n"
        f"            {{% endif %}}\n"
        f"            <div class=\"card-content\">\n"
        f"                <div class=\"verse-number\">\n"
        f"                    <span data-lang=\"en\">{num_en}</span>\n"
        f"                    <span data-lang=\"hi\">{num_hi}</span>\n"
        f"                </div>\n"
        f"                <div class=\"verse-title\">\n"
        f"                    <span data-lang=\"en\">{{{{ {var}.title_en }}}}</span>\n"
        f"                    <span data-lang=\"hi\">{{{{ {var}.title_hi }}}}</span>\n"
        f"                </div>\n"
        f"                {{% if {var}.puranic_context %}}\n"
        f"                <div class=\"puranic-badge\">\n"
        f"                    <span class=\"badge-icon\">📚</span>\n"
        f"                </div>\n"
        f"                {{% endif %}}\n"
        f"            </div>\n"
        f"        </a>"
    )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_index_html(collection_key: str, config: Dict, sections: List[Dict]) -> str:
    """Assemble the complete index.html Liquid template."""
    name_en = config.get("name_en", collection_key.replace("-", " ").title())
    name_hi = config.get("name_hi", "")
    coll_icon = config.get("icon", "📿")
    permalink_base = config.get("permalink_base", f"/{collection_key}/").rstrip("/") + "/"

    # Build section blocks
    blocks: List[str] = []
    for section in sections:
        prefix = section["prefix"]
        verse_ids = section["verse_ids"]
        qualifier = section.get("qualifier")
        icon, en, hi = _section_label(prefix, qualifier)

        if section["is_loop"]:
            blocks.append(_loop_section(prefix, collection_key, icon, en, hi))
        else:
            blocks.append(_individual_section(verse_ids, collection_key, icon, en, hi))

    sections_html = "\n".join(blocks)

    return f"""---
layout: default
title: {name_en}
collection_key: {collection_key}
---
{{% assign t_en = site.data.translations.en %}}
{{% assign t_hi = site.data.translations.hi %}}

<div class="hero-section">
    <div class="title-image-container">
        <img src="{{{{ '/images/{collection_key}/modern-minimalist/title-page.png' | relative_url }}}}" alt="{name_en} Title Page" class="title-page-image" data-themed-image="title-page.png">
    </div>
    <div class="quick-actions">
        <a href="{{{{ '{permalink_base}book' | relative_url }}}}?collection={collection_key}" class="btn-secondary">📕 <span data-lang="en">Generate Book</span><span data-lang="hi">पुस्तक बनाएं</span></a>
    </div>
    <div class="collection-meta">
        <span class="puranic-legend-compact">📚 <span data-lang="en">Some verses have Puranic stories</span><span data-lang="hi">कुछ पदों में पौराणिक कथाएं हैं</span></span>
    </div>
</div>

<section class="verse-navigation">
    <h2>{coll_icon} <span data-lang="en">{name_en}</span><span data-lang="hi">{name_hi}</span></h2>
{sections_html}
</section>
"""


# ---------------------------------------------------------------------------
# Project I/O
# ---------------------------------------------------------------------------

def load_collections(project_dir: Path) -> Dict:
    path = project_dir / "_data" / "collections.yml"
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_sequence(collection_key: str, project_dir: Path) -> Optional[List[str]]:
    """Read _meta.sequence from data/verses/{collection}.yaml if present."""
    for ext in ("yaml", "yml"):
        path = project_dir / "data" / "verses" / f"{collection_key}.{ext}"
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                meta = data.get("_meta") or {}
                seq = meta.get("sequence")
                if isinstance(seq, list):
                    return [str(v) for v in seq]
            except Exception:
                pass
    return None


def scaffold_collection(collection_key: str, project_dir: Path, overwrite: bool = False) -> bool:
    """
    Generate index.html for one collection. Returns True on success.
    """
    collections = load_collections(project_dir)
    if collection_key not in collections:
        print(f"Error: '{collection_key}' not found in _data/collections.yml", file=sys.stderr)
        return False

    config = collections[collection_key]
    permalink_base = config.get("permalink_base", f"/{collection_key}/")
    output_dir_name = permalink_base.strip("/")
    output_file = project_dir / output_dir_name / "index.html"

    if output_file.exists() and not overwrite:
        print(f"  ⚠ Skipped {output_file} (already exists — use --overwrite to regenerate)")
        return True

    verses_dir = project_dir / "_verses" / collection_key
    sequence = _load_sequence(collection_key, project_dir)
    sections = detect_sections(verses_dir, sequence=sequence)

    if not sections:
        print(f"  ⚠ No verse files found in {verses_dir} — generating template with empty sections")

    html = generate_index_html(collection_key, config, sections)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")

    verse_count = sum(len(s["verse_ids"]) for s in sections)
    section_count = len(sections)
    action = "Regenerated" if output_file.exists() else "Created"
    print(f"  ✓ {action} {output_file} ({section_count} section(s), {verse_count} verse(s))")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a collection index.html from _data/collections.yml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scaffold one collection
  verse-init-collection --collection bajrang-baan

  # Regenerate (overwrite existing)
  verse-init-collection --collection bajrang-baan --overwrite

  # Scaffold all enabled collections
  verse-init-collection --all

  # Scaffold all, overwriting existing
  verse-init-collection --all --overwrite
        """,
    )
    parser.add_argument("--collection", metavar="KEY", help="Collection key from _data/collections.yml")
    parser.add_argument("--all", action="store_true", help="Scaffold all enabled collections")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing index.html files")
    parser.add_argument("--project-dir", default=".", metavar="DIR", help="Project root directory (default: .)")

    args = parser.parse_args()

    if not args.collection and not args.all:
        parser.error("Specify --collection KEY or --all")

    project_dir = Path(args.project_dir).resolve()

    if args.all:
        collections = load_collections(project_dir)
        keys = [k for k, v in collections.items() if isinstance(v, dict) and v.get("enabled", True)]
        if not keys:
            print("No enabled collections found in _data/collections.yml")
            sys.exit(0)
        print(f"Scaffolding {len(keys)} collection(s)...")
        for key in keys:
            scaffold_collection(key, project_dir, overwrite=args.overwrite)
    else:
        scaffold_collection(args.collection, project_dir, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
