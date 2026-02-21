#!/usr/bin/env python3
"""
Generate Puranic context boxes for verse files.

This command uses AI to identify relevant Puranic references (stories, characters,
concepts, etymologies) and injects a puranic_context block into the verse
file's frontmatter.

When indexed sources are available (data/puranic-references.yml + data/puranic-index/),
retrieval-augmented generation (RAG) is used to ground the context in actual source
texts. Otherwise, GPT-4 free recall is used as a fallback.

Usage:
    # Generate for a specific verse
    verse-puranic-context --collection hanuman-chalisa --verse chaupai-15

    # Generate for all verses missing context
    verse-puranic-context --collection bajrang-baan --all

    # Force regenerate even if context exists
    verse-puranic-context --collection hanuman-chalisa --verse chaupai-18 --regenerate

Requirements:
    - OPENAI_API_KEY environment variable
"""

import os
import sys
import json
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed")
    print("Install with: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed")
    print("Install with: pip install openai")
    sys.exit(1)

load_dotenv()

VALID_TYPES = {"story", "concept", "character", "etymology", "practice", "cross_reference"}
VALID_PRIORITIES = {"high", "medium", "low"}

SYSTEM_PROMPT = """You are an expert in Hindu scriptures, Puranas, and devotional literature
(bhakti). You generate structured Puranic context boxes for verses from sacred texts like
Hanuman Chalisa, Sundar Kaand, Bajrang Baan, and Sankat Mochan Hanumanashtak.

Each context entry must be a YAML object with these fields:
  id: unique-slug (kebab-case)
  type: story | concept | character | etymology | practice | cross_reference
  priority: high | medium | low
  title:
    en: "English title"
    hi: "Hindi title in Devanagari"
  icon: single emoji
  story_summary:
    en: "2-4 sentence summary"
    hi: "Same in Hindi Devanagari"
  theological_significance:
    en: "2-4 sentences on spiritual meaning"
    hi: "Same in Hindi Devanagari"
  practical_application:
    en: "2-4 sentences on practical use"
    hi: "Same in Hindi Devanagari"
  source_texts:
    - text: "Scripture name"
      section: "Book/chapter/kanda"
  related_verses: []

Rules:
- Generate 1-3 entries per verse (only the most relevant references)
- For short invocations, closing verses, or verses with no meaningful Puranic
  content, return an empty list []
- Prioritise accuracy over quantity
- All Hindi text must be in Devanagari script
- Return ONLY valid YAML — no markdown fences, no explanation
- CITATION RULES (strictly enforced):
  * Every entry MUST have a genuine section reference (e.g. "Rudrasamhita, Chapter 12")
    sourced from the retrieved episode metadata provided below
  * Do NOT set section to "Not directly mentioned", "Unknown", "Various", or any
    vague placeholder — omit the entire entry instead
  * Do NOT cite scriptures that were not provided in the retrieved episodes
    (e.g. do not cite Ramayana or Mahabharata unless those episodes were retrieved)
  * If no retrieved episode provides a direct, citable reference for an entry, return []
  * Do NOT generate entries from your general knowledge or other scriptures —
    every entry must be derivable from the episodes listed above


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def parse_verse_file(verse_file: Path) -> Tuple[Optional[Dict], Optional[str]]:
    """Parse verse frontmatter and body. Returns (frontmatter, body)."""
    if not verse_file.exists():
        return None, None
    try:
        content = verse_file.read_text(encoding='utf-8')
        if not content.startswith('---'):
            return {}, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except Exception as e:
        print(f"  ✗ Error parsing {verse_file.name}: {e}", file=sys.stderr)
        return None, None


def update_verse_file(verse_file: Path, frontmatter: Dict, body: str) -> bool:
    """Write updated frontmatter back to verse file."""
    try:
        content = "---\n"
        content += yaml.dump(frontmatter, allow_unicode=True, sort_keys=False,
                             default_flow_style=False)
        content += "---"
        content += body
        verse_file.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  ✗ Error writing {verse_file.name}: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------------------------

def load_project_defaults(project_dir: Path) -> Dict:
    """
    Load defaults from _data/verse-config.yml.
    Returns the contents of the 'defaults' key, or {} if not found.
    """
    config_file = project_dir / "_data" / "verse-config.yml"
    if not config_file.exists():
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("defaults") or {}
    except Exception as e:
        print(f"  Warning: Could not read verse-config.yml: {e}", file=sys.stderr)
        return {}


def load_collection_subject(collection_key: str, project_dir: Path) -> Tuple[Optional[str], str]:
    """
    Resolve subject and subject_type for a collection using the hierarchy:
      1. Collection-level subject in _data/collections.yml  (highest priority)
      2. Project-level defaults.subject in _data/verse-config.yml
      3. None  (caller should error when indexed sources exist)
    Returns (subject, subject_type).
    """
    # 1. Collection-level
    collections_file = project_dir / "_data" / "collections.yml"
    if collections_file.exists():
        try:
            with open(collections_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            config = data.get(collection_key, {})
            if isinstance(config, dict):
                subject = config.get("subject") or None
                subject_type = config.get("subject_type") or None
                if subject:
                    return subject, subject_type or "deity"
        except Exception as e:
            print(f"  Warning: Could not read collections.yml: {e}", file=sys.stderr)

    # 2. Project-level defaults
    defaults = load_project_defaults(project_dir)
    subject = defaults.get("subject") or None
    subject_type = defaults.get("subject_type") or "deity"
    return subject, subject_type


def load_puranic_references(project_dir: Path) -> Dict:
    """Load data/puranic-references.yml, return {} if not found."""
    ref_file = project_dir / "data" / "puranic-references.yml"
    if not ref_file.exists():
        return {}
    try:
        with open(ref_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {k: v for k, v in data.items() if v.get("enabled", False)}
    except Exception as e:
        print(f"  Warning: Could not load puranic-references.yml: {e}", file=sys.stderr)
        return {}


def load_index_meta(key: str, project_dir: Path) -> Optional[Dict]:
    """Load _meta from data/puranic-index/<key>.yml, return None if not found."""
    index_file = project_dir / "data" / "puranic-index" / f"{key}.yml"
    if not index_file.exists():
        return None
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data.get("_meta")
        return None
    except Exception:
        return None


def load_episode_index(key: str, project_dir: Path) -> List[Dict]:
    """Load episodes from data/puranic-index/<key>.yml, return [] if not found.
    Handles both new format ({_meta, episodes}) and legacy bare-list format."""
    index_file = project_dir / "data" / "puranic-index" / f"{key}.yml"
    if not index_file.exists():
        return []
    try:
        with open(index_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data.get("episodes") or []
        return data or []  # legacy: bare list
    except Exception as e:
        print(f"  Warning: Could not load episode index for '{key}': {e}", file=sys.stderr)
        return []


def load_episode_embeddings(key: str, project_dir: Path) -> List[Dict]:
    """Load data/embeddings/<key>.json, return [] if not found."""
    emb_file = project_dir / "data" / "embeddings" / f"{key}.json"
    if not emb_file.exists():
        return []
    try:
        with open(emb_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("episodes", [])
    except Exception as e:
        print(f"  Warning: Could not load embeddings for '{key}': {e}", file=sys.stderr)
        return []


def load_embeddings_model(key: str, project_dir: Path) -> Optional[str]:
    """Read the model name stored in data/embeddings/<key>.json metadata."""
    emb_file = project_dir / "data" / "embeddings" / f"{key}.json"
    if not emb_file.exists():
        return None
    try:
        with open(emb_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("model")
    except Exception:
        return None


def provider_from_model(model: str) -> str:
    """Map a model name to its provider key for initialize_provider."""
    if model and model.startswith("cohere."):
        return "bedrock-cohere"
    return "openai"


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Dot product of two L2-normalised vectors (Cohere embeddings are normalised)."""
    try:
        import numpy as np
        return float(np.dot(a, b))
    except ImportError:
        # Pure-Python fallback
        dot = sum(x * y for x, y in zip(a, b))
        return dot


def search_episodes(
    query_embedding: List[float],
    all_episodes: List[Dict],
    all_embeddings: List[Dict],
    top_k: int = 8,
) -> List[Dict]:
    """Return the top-k episodes by cosine similarity to the query embedding."""
    # Build a lookup from episode id → embedding vector
    emb_by_id: Dict[str, List[float]] = {
        e["id"]: e["embedding"] for e in all_embeddings if "id" in e and "embedding" in e
    }

    scored = []
    for ep in all_episodes:
        ep_id = ep.get("id", "")
        if ep_id not in emb_by_id:
            continue
        score = cosine_similarity(query_embedding, emb_by_id[ep_id])
        scored.append((score, ep))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ep for _, ep in scored[:top_k]]


def filter_episodes_by_subject(episodes: List[Dict], subject: str) -> List[Dict]:
    """
    Filter retrieved episodes to those where the subject appears as a participant.
    Checks episode id, keywords, and summary_en (case-insensitive).
    Returns the filtered list; if nothing matches, returns the original list
    so the generation prompt can still apply the constraint.
    """
    tokens = [t.lower() for t in subject.split()]

    def matches(ep: Dict) -> bool:
        haystack = " ".join([
            ep.get("id", ""),
            " ".join(ep.get("keywords", [])),
            ep.get("summary_en", ""),
            ep.get("summary_hi", ""),
        ]).lower()
        return any(token in haystack for token in tokens)

    filtered = [ep for ep in episodes if matches(ep)]
    return filtered if filtered else episodes


def embed_verse_for_search(
    frontmatter: Dict, verse_id: str, project_dir: Path, provider: str = "openai"
) -> Optional[List[float]]:
    """
    Embed the verse for RAG search using the same provider as the stored embeddings.
    Returns the embedding vector or None on failure.
    """
    try:
        from verse_sdk.embeddings.generate_embeddings import initialize_provider, get_bedrock_embedding
    except ImportError as e:
        print(f"  Warning: Could not import embedding module: {e}", file=sys.stderr)
        return None

    # Build search text from verse fields
    parts = []
    for field in ("devanagari", "transliteration"):
        val = frontmatter.get(field)
        if val:
            parts.append(str(val))
    for field in ("translation", "interpretive_meaning", "literal_translation"):
        val = frontmatter.get(field)
        if isinstance(val, dict):
            val = val.get("en", "")
        if val:
            parts.append(str(val)[:300])
    if not parts:
        parts.append(verse_id)

    text = " ".join(parts)

    try:
        embed_fn, client, config = initialize_provider(provider)
        backend = config.get("backend", "openai")
        if backend == "bedrock":
            return get_bedrock_embedding(text, client, config, input_type="search_query")
        elif backend == "openai":
            return embed_fn(text, client, config["model"])
        else:
            return embed_fn(text, client)
    except Exception as e:
        print(f"  Warning: Embedding failed for verse '{verse_id}': {e}", file=sys.stderr)
        return None


def format_retrieved_episodes(episodes: List[Dict]) -> str:
    """Format retrieved episodes into a readable context block for the prompt."""
    if not episodes:
        return ""
    lines = ["Relevant Puranic sources (use these as grounding material):"]
    for i, ep in enumerate(episodes, 1):
        ep_id = ep.get("id", f"episode-{i}")
        summary = ep.get("summary_en", "")
        keywords = ep.get("keywords", [])
        source = ep.get("source", {})
        book = source.get("book", "") if isinstance(source, dict) else ""
        sarga = source.get("sarga", "") if isinstance(source, dict) else ""
        source_ref = f"{book}" + (f", {sarga}" if sarga else "")
        lines.append(f"\n[{i}] {ep_id}")
        if source_ref:
            lines.append(f"    Source: {source_ref}")
        if keywords:
            lines.append(f"    Keywords: {', '.join(keywords)}")
        if summary:
            lines.append(f"    Summary: {summary}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt builder + GPT-4 call
# ---------------------------------------------------------------------------

def build_prompt(frontmatter: Dict, verse_id: str) -> str:
    """Build the user prompt from verse frontmatter fields."""
    devanagari = frontmatter.get('devanagari', '')
    transliteration = frontmatter.get('transliteration', '')
    title_en = frontmatter.get('title_en', verse_id)

    meaning_parts = []
    for field in ('translation', 'interpretive_meaning', 'literal_translation'):
        val = frontmatter.get(field)
        if isinstance(val, dict):
            val = val.get('en', '')
        if val:
            meaning_parts.append(f"{field}: {val}")

    story = frontmatter.get('story', {})
    if isinstance(story, dict):
        story = story.get('en', '')
    story_text = str(story)[:800] if story else ''

    prompt = f"""Verse: {title_en}
Devanagari: {devanagari}
Transliteration: {transliteration}
"""
    if meaning_parts:
        prompt += "\n".join(meaning_parts) + "\n"
    if story_text:
        prompt += f"\nStory/Context: {story_text}\n"

    prompt += """
Generate Puranic context entries for this verse as a YAML list.
Return [] if the verse has no meaningful Puranic content."""
    return prompt


_VAGUE_SECTIONS = {
    "not directly mentioned", "not mentioned", "not explicitly mentioned",
    "not directly cited", "not explicitly cited",
    "not directly applicable", "not directly applicable",
    "not directly referenced", "not explicitly referenced",
    "not directly stated", "not explicitly stated",
    "unknown", "various", "n/a", "na", "none", "unclear",
    "unspecified", "not specified", "not available", "not applicable",
}


def _reject_uncited_entries(
    entries: List[Dict],
    indexed_source_names: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Drop any context entry where every source_texts item has:
    - A missing or vague section (placeholder phrases or bare numbers), OR
    - A source name not found in the indexed sources (cross-scripture hallucination).
    """
    allowed_names: Optional[set] = None
    if indexed_source_names:
        allowed_names = {n.lower() for n in indexed_source_names}

    kept = []
    for entry in entries:
        source_texts = entry.get("source_texts") or []
        valid = []
        for s in source_texts:
            if not isinstance(s, dict):
                continue
            section = str(s.get("section", "")).strip()
            # Reject vague/placeholder sections
            if section == "" or section.lower() in _VAGUE_SECTIONS:
                continue
            # Reject bare numeric sections ("71" alone — no Purana name)
            if section.isdigit():
                continue
            # Reject if cited text is not one of the indexed sources
            if allowed_names is not None:
                text_name = str(s.get("text", "")).strip().lower()
                if text_name and not any(
                    allowed in text_name or text_name in allowed
                    for allowed in allowed_names
                ):
                    continue
            valid.append(s)

        if valid:
            entry["source_texts"] = valid
            kept.append(entry)
        else:
            ep_id = entry.get("id", "?")
            print(f"    ⚠ Dropped entry '{ep_id}': no citable section reference from indexed sources", file=sys.stderr)
    return kept


def _filter_by_subject_participation(
    entries: List[Dict],
    subject: str,
    subject_type: str,
    client,
) -> List[Dict]:
    """
    Use GPT-4o-mini to verify each entry involves the subject as a direct
    participant (not merely mentioned or symbolically referenced).
    Rejects entries where the subject is only thematically connected.
    """
    if not entries:
        return entries

    kept = []
    for entry in entries:
        ep_id = entry.get("id", "?")
        title = entry.get("title", {})
        if isinstance(title, dict):
            title = title.get("en", "")
        summary = entry.get("story_summary", {})
        if isinstance(summary, dict):
            summary = summary.get("en", "")

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Does the following story directly involve the {subject_type} {subject} "
                            f"as an active participant (not merely mentioned, symbolically referenced, "
                            f"or only thematically connected)?\n\n"
                            f"Title: {title}\n"
                            f"Summary: {summary}\n\n"
                            f"Answer with only 'yes' or 'no'."
                        ),
                    }
                ],
                temperature=0,
                max_tokens=5,
            )
            answer = resp.choices[0].message.content.strip().lower()
            if answer.startswith("yes"):
                kept.append(entry)
            else:
                print(
                    f"    ⚠ Dropped entry '{ep_id}': {subject} is not a direct participant",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"    ⚠ Subject validation failed for '{ep_id}': {e} — keeping entry", file=sys.stderr)
            kept.append(entry)

    return kept


def generate_puranic_context(
    frontmatter: Dict,
    verse_id: str,
    retrieved_episodes: Optional[List[Dict]] = None,
    indexed_source_names: Optional[List[str]] = None,
    subject: Optional[str] = None,
    subject_type: Optional[str] = None,
) -> Optional[List]:
    """Call GPT-4o to generate puranic_context entries. Returns a list or None on error."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = build_prompt(frontmatter, verse_id)

    system = SYSTEM_PROMPT
    if retrieved_episodes:
        context_block = format_retrieved_episodes(retrieved_episodes)
        system = SYSTEM_PROMPT + "\n\n" + context_block
    if indexed_source_names:
        names = ", ".join(indexed_source_names)
        system += f"\n\nIMPORTANT: The source_texts field must only cite the following indexed sources: {names}. Do not cite any other texts."
    if subject:
        label = f"{subject_type} {subject}" if subject_type else subject
        system += f"\n\nIMPORTANT: Only include context entries that directly involve {label} as a primary or secondary participant, or that are theologically necessary to understand this verse about {label}. Omit entries about other deities or figures unless they directly interact with {label} in the episode."

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        parsed = yaml.safe_load(raw)
        if parsed is None:
            return []
        if not isinstance(parsed, list):
            print(f"  ⚠ Unexpected response format (not a list)", file=sys.stderr)
            return None

        # Fix 1+3: reject vague sections and cross-scripture citations
        result = _reject_uncited_entries(parsed, indexed_source_names=indexed_source_names)

        # Fix 2: reject entries where subject is not a direct participant
        if subject and result:
            label = subject_type or "deity"
            print(f"    → Validating subject participation for {len(result)} entr{'y' if len(result) == 1 else 'ies'}...", file=sys.stderr)
            result = _filter_by_subject_participation(result, subject, label, client)

        return result

    except yaml.YAMLError as e:
        print(f"  ✗ YAML parse error in AI response: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ✗ API error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def process_verse(
    verse_file: Path,
    regenerate: bool = False,
    project_dir: Optional[Path] = None,
    subject: Optional[str] = None,
    subject_type: Optional[str] = None,
) -> str:
    """
    Process a single verse file.

    Returns: 'added' | 'skipped' | 'regenerated' | 'empty' | 'error'
    """
    if project_dir is None:
        project_dir = Path.cwd()

    frontmatter, body = parse_verse_file(verse_file)
    if frontmatter is None:
        return 'error'

    verse_id = verse_file.stem
    already_has_context = bool(frontmatter.get('puranic_context'))

    if already_has_context and not regenerate:
        print(f"  ⊘ {verse_id}: Already has puranic_context, skipping (use --regenerate to overwrite)")
        return 'skipped'

    # --- RAG: try to retrieve grounding context ---
    retrieved_episodes: Optional[List[Dict]] = None
    sources = load_puranic_references(project_dir)

    if sources:
        # Detect provider from _meta in index file (authoritative), fall back to embeddings JSON
        provider = "openai"
        for key in sources:
            meta = load_index_meta(key, project_dir)
            if meta and meta.get("embedding_provider"):
                provider = meta["embedding_provider"]
                break
            model = load_embeddings_model(key, project_dir)
            if model:
                provider = provider_from_model(model)
                break

        print(f"  → {verse_id}: Embedding verse for RAG search ({len(sources)} source(s), provider: {provider})...")
        query_embedding = embed_verse_for_search(frontmatter, verse_id, project_dir, provider=provider)

        if query_embedding:
            all_episodes: List[Dict] = []
            all_embeddings: List[Dict] = []
            for key in sources:
                all_episodes.extend(load_episode_index(key, project_dir))
                all_embeddings.extend(load_episode_embeddings(key, project_dir))

            if all_episodes and all_embeddings:
                retrieved_episodes = search_episodes(query_embedding, all_episodes, all_embeddings)
                if subject and retrieved_episodes:
                    filtered = filter_episodes_by_subject(retrieved_episodes, subject)
                    if len(filtered) < len(retrieved_episodes):
                        print(f"  → {verse_id}: Filtered to {len(filtered)}/{len(retrieved_episodes)} episodes matching subject '{subject}'")
                    retrieved_episodes = filtered
                else:
                    print(f"  → {verse_id}: Retrieved {len(retrieved_episodes)} relevant episode(s)")
            else:
                print(f"  ⚠ {verse_id}: Sources registered but no indexed episodes found")
        else:
            print(f"  ⚠ {verse_id}: Could not embed verse for search, falling back to free recall")
    else:
        print(f"  ⚠ {verse_id}: No indexed Puranic sources found.")
        print(f"    Run 'verse-index-sources --file data/sources/<file>' to index source documents.")
        answer = input("    Continue with GPT-4 free recall? [y/N] ").strip().lower()
        if answer != "y":
            print(f"  ⊘ {verse_id}: Skipped")
            return 'skipped'

    indexed_source_names = [v.get("name", k) for k, v in sources.items()] if sources else None

    print(f"  → {verse_id}: Generating Puranic context{'  (RAG-grounded)' if retrieved_episodes else ''}...")
    entries = generate_puranic_context(
        frontmatter, verse_id,
        retrieved_episodes=retrieved_episodes,
        indexed_source_names=indexed_source_names,
        subject=subject,
        subject_type=subject_type,
    )

    if entries is None:
        return 'error'

    if len(entries) == 0:
        print(f"  ○ {verse_id}: No Puranic content identified, skipping")
        return 'empty'

    frontmatter['puranic_context'] = entries
    if not update_verse_file(verse_file, frontmatter, body):
        return 'error'

    action = 'regenerated' if already_has_context else 'added'
    print(f"  ✓ {verse_id}: {len(entries)} context entr{'y' if len(entries) == 1 else 'ies'} {action}")
    return action


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for verse-puranic-context command."""
    parser = argparse.ArgumentParser(
        description="Generate Puranic context boxes for verse files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for a specific verse (by verse ID)
  verse-puranic-context --collection hanuman-chalisa --verse chaupai-15

  # Generate for all verses missing context
  verse-puranic-context --collection bajrang-baan --all

  # Force regenerate even if context already exists
  verse-puranic-context --collection hanuman-chalisa --verse chaupai-18 --regenerate

  # Regenerate all verses in a collection
  verse-puranic-context --collection sundar-kaand --all --regenerate

Note:
  - subject and subject_type are read from _data/collections.yml (add them there)
  - Uses RAG retrieval when indexed sources are available (data/puranic-references.yml)
  - Falls back to GPT-4 free recall with confirmation prompt if no sources indexed
  - Skips verses that already have puranic_context (use --regenerate to overwrite)
  - Requires OPENAI_API_KEY environment variable
        """
    )

    parser.add_argument(
        "--collection",
        required=True,
        metavar="KEY",
        help="Collection key (e.g., hanuman-chalisa, sundar-kaand)"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--verse",
        metavar="ID",
        help="Verse ID to process (e.g., chaupai-15, doha-01)"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all verses in the collection"
    )

    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Overwrite existing puranic_context entries"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    verses_dir = args.project_dir / "_verses" / args.collection
    if not verses_dir.exists():
        print(f"✗ Error: Collection directory not found: {verses_dir}")
        sys.exit(1)

    # Determine verse files to process
    if args.all:
        verse_files = sorted(verses_dir.glob("*.md"))
        if not verse_files:
            print(f"✗ Error: No verse files found in {verses_dir}")
            sys.exit(1)
    else:
        verse_file = verses_dir / f"{args.verse}.md"
        if not verse_file.exists():
            print(f"✗ Error: Verse file not found: {verse_file}")
            sys.exit(1)
        verse_files = [verse_file]

    # Read subject/subject_type from collections.yml
    subject, subject_type = load_collection_subject(args.collection, args.project_dir)

    # If indexed sources are available and no subject is configured, error clearly
    sources = load_puranic_references(args.project_dir)
    if sources and not subject:
        print(f"✗ Error: Indexed sources are available but 'subject' is not configured for collection '{args.collection}'.")
        print(f"  Add the following to _data/collections.yml under '{args.collection}':")
        print(f"")
        print(f"    subject: <primary deity or subject>   # e.g. Hanuman")
        print(f"    subject_type: deity                   # e.g. deity, avatar, concept")
        print(f"")
        print(f"  This is required to filter RAG results and validate context entries.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("PURANIC CONTEXT GENERATION")
    print("=" * 60)
    print(f"\nCollection : {args.collection}")
    print(f"Verses     : {'all (' + str(len(verse_files)) + ')' if args.all else args.verse}")
    print(f"Regenerate : {'yes' if args.regenerate else 'no (skip existing)'}")
    if subject:
        print(f"Subject    : {subject} ({subject_type})")
    if sources:
        print(f"RAG sources: {len(sources)} indexed ({', '.join(sources.keys())})")
    else:
        print(f"RAG sources: none (will prompt for free-recall fallback)")
    print()

    counts = {'added': 0, 'regenerated': 0, 'skipped': 0, 'empty': 0, 'error': 0}

    try:
        for verse_file in verse_files:
            result = process_verse(
                verse_file,
                regenerate=args.regenerate,
                project_dir=args.project_dir,
                subject=subject,
                subject_type=subject_type,
            )
            counts[result] = counts.get(result, 0) + 1
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if counts['added']:
        print(f"  ✓ Added    : {counts['added']}")
    if counts['regenerated']:
        print(f"  ✓ Updated  : {counts['regenerated']}")
    if counts['empty']:
        print(f"  ○ No content : {counts['empty']}")
    if counts['skipped']:
        print(f"  ⊘ Skipped  : {counts['skipped']}")
    if counts['error']:
        print(f"  ✗ Errors   : {counts['error']}")
    print()

    sys.exit(1 if counts['error'] == len(verse_files) else 0)


if __name__ == "__main__":
    main()
