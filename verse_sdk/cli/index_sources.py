#!/usr/bin/env python3
"""
Index Puranic source texts (PDFs, TXTs) into episodes + embeddings.

This command extracts text from source documents, uses GPT-4o to structure
episodes, embeds them via Bedrock Cohere, and writes the indexed data to:
  - data/puranic-index/<key>.yml      (episode metadata)
  - data/embeddings/<key>.json        (episode embeddings)
  - data/puranic-references.yml       (registry of indexed sources)

Usage:
    verse-index-sources --file data/sources/valmiki-ramayana.pdf
    verse-index-sources --file data/sources/devi-bhagavata.txt --force
    verse-index-sources --file data/sources/notes.md --provider bedrock-cohere
"""

import os
import sys
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

load_dotenv()

CHUNK_SIZE = 1500  # characters per chunk

EPISODE_SYSTEM_PROMPT = """You are an expert in Hindu scriptures and Puranic literature.
Given a passage from a source text, extract structured episodes as a YAML list.

Each episode must have these fields:
  id: unique-slug (kebab-case, globally unique across the source)
  type: story | character | concept | etymology | practice | event
  keywords:
    - keyword1
    - keyword2
  source:
    book: "Name of book/text"
    sarga: "Chapter/section reference if known, else empty string"
  summary_en: "2-4 sentence summary in English"
  summary_hi: "Same summary in Hindi Devanagari"

Rules:
- Only extract episodes with actual narrative/mythological content
- Skip boilerplate, table of contents, indices, and editorial notes
- Use globally unique IDs (e.g. rama-exile-episode, hanuman-birth-story)
- All Hindi text must be in Devanagari script
- Return ONLY valid YAML — no markdown fences, no explanation
- Return [] if the passage has no extractable Puranic episodes"""


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(1)

    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
    return "\n\n".join(texts)


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from PDF, TXT, or MD file."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8")
    else:
        print(f"Error: Unsupported file format '{suffix}'. Supported: .pdf, .txt, .md")
        sys.exit(1)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Split text into ~chunk_size character chunks on paragraph boundaries.
    Accumulates paragraphs until the limit is reached, then starts a new chunk.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_len = len(para)
        if current_len + para_len > chunk_size and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len + 2  # +2 for the \n\n separator

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def extract_episodes_from_chunk(
    chunk: str, source_key: str, openai_client: OpenAI, chunk_idx: int, total_chunks: int
) -> List[Dict]:
    """Call GPT-4o to extract structured episodes from a text chunk."""
    prompt = f"""Source: {source_key}
Passage (chunk {chunk_idx + 1}/{total_chunks}):

{chunk}

Extract Puranic episodes from this passage as a YAML list. Return [] if none."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": EPISODE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
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
            print(f"    Warning: Unexpected response format (not a list), skipping chunk", file=sys.stderr)
            return []
        return parsed

    except yaml.YAMLError as e:
        print(f"    Warning: YAML parse error in chunk {chunk_idx + 1}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"    Warning: API error on chunk {chunk_idx + 1}: {e}", file=sys.stderr)
        return []


def deduplicate_episodes(episodes: List[Dict]) -> List[Dict]:
    """Deduplicate by episode ID. Later chunk wins on conflict."""
    seen: Dict[str, Dict] = {}
    for ep in episodes:
        ep_id = ep.get("id", "")
        if ep_id:
            seen[ep_id] = ep
    return list(seen.values())


def embed_episodes(
    episodes: List[Dict], embed_fn, client, config
) -> List[Dict]:
    """
    Generate embeddings for each episode.
    Text = summary_en + " " + summary_hi, input_type="search_document".
    Returns list of {"id": ..., "embedding": [...]} dicts.
    """
    from verse_sdk.embeddings.generate_embeddings import get_bedrock_embedding
    import time

    results = []
    for i, ep in enumerate(episodes):
        ep_id = ep.get("id", f"episode-{i}")
        summary_en = ep.get("summary_en", "")
        summary_hi = ep.get("summary_hi", "")
        text = f"{summary_en} {summary_hi}".strip()

        if not text:
            print(f"    Warning: Episode '{ep_id}' has no summary, skipping embedding")
            continue

        backend = config.get("backend", "openai")
        if backend == "bedrock":
            embedding = get_bedrock_embedding(text, client, config, input_type="search_document")
        elif backend == "openai":
            embedding = embed_fn(text, client, config["model"])
        else:
            embedding = embed_fn(text, client)

        if embedding is None:
            print(f"    Warning: Failed to embed episode '{ep_id}'", file=sys.stderr)
            continue

        results.append({"id": ep_id, "embedding": embedding})

        if backend in ("bedrock", "openai"):
            time.sleep(0.1)

    return results


def load_puranic_references(project_dir: Path) -> Dict:
    """Load data/puranic-references.yml, return {} if not found."""
    ref_file = project_dir / "data" / "puranic-references.yml"
    if not ref_file.exists():
        return {}
    with open(ref_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_puranic_references(refs: Dict, project_dir: Path) -> None:
    """Write data/puranic-references.yml."""
    ref_file = project_dir / "data" / "puranic-references.yml"
    ref_file.parent.mkdir(parents=True, exist_ok=True)
    with open(ref_file, "w", encoding="utf-8") as f:
        yaml.dump(refs, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def is_already_indexed(key: str, project_dir: Path) -> bool:
    """Return True if key exists in puranic-references.yml and index file exists."""
    refs = load_puranic_references(project_dir)
    if key not in refs:
        return False
    index_file = project_dir / "data" / "puranic-index" / f"{key}.yml"
    return index_file.exists()


def main():
    """Main entry point for verse-index-sources command."""
    parser = argparse.ArgumentParser(
        description="Index Puranic source texts into episodes and embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a PDF source
  verse-index-sources --file data/sources/valmiki-ramayana.pdf

  # Index a text file, force re-index
  verse-index-sources --file data/sources/devi-bhagavata.txt --force

  # Use a specific embedding provider
  verse-index-sources --file data/sources/notes.md --provider bedrock-cohere

Note:
  - Outputs are written to data/puranic-index/<key>.yml and data/embeddings/<key>.json
  - Requires OPENAI_API_KEY and (for bedrock-cohere) AWS credentials
        """,
    )

    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        metavar="PATH",
        help="Path to source file (.pdf, .txt, or .md)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-index even if this source has already been indexed",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--provider",
        choices=["bedrock-cohere", "openai"],
        default="bedrock-cohere",
        help="Embedding provider (default: bedrock-cohere)",
    )

    args = parser.parse_args()

    # Validate environment
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Validate input file
    source_file = args.file
    if not source_file.is_absolute():
        source_file = args.project_dir / source_file
    if not source_file.exists():
        print(f"Error: Source file not found: {source_file}")
        sys.exit(1)

    # Derive key from filename stem
    key = source_file.stem  # e.g. valmiki-ramayana.pdf → valmiki-ramayana

    print()
    print("=" * 60)
    print("SOURCE INDEXING")
    print("=" * 60)
    print(f"\nSource     : {source_file.name}")
    print(f"Key        : {key}")
    print(f"Format     : {source_file.suffix.lstrip('.')}")
    print(f"Provider   : {args.provider}")
    print(f"Project dir: {args.project_dir}")
    print()

    # Guard: already indexed?
    if is_already_indexed(key, args.project_dir) and not args.force:
        print(f"Source '{key}' is already indexed.")
        print("Use --force to re-index.")
        sys.exit(0)

    # Step 1: Extract text
    print(f"Extracting text from {source_file.name}...")
    text = extract_text_from_file(source_file)
    print(f"  Extracted {len(text):,} characters")

    # Step 2: Chunk
    chunks = chunk_text(text)
    print(f"  Split into {len(chunks)} chunks (~{CHUNK_SIZE} chars each)")
    print()

    # Step 3: Extract episodes via GPT-4o
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    all_episodes: List[Dict] = []

    print("Extracting episodes via GPT-4o...")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i + 1}/{len(chunks)}...", end=" ", flush=True)
        eps = extract_episodes_from_chunk(chunk, key, openai_client, i, len(chunks))
        print(f"{len(eps)} episode(s)")
        all_episodes.extend(eps)

    print(f"\n  Raw episodes: {len(all_episodes)}")

    # Step 4: Deduplicate
    episodes = deduplicate_episodes(all_episodes)
    print(f"  After dedup : {len(episodes)} unique episodes")
    print()

    if not episodes:
        print("Warning: No episodes extracted. Check source content and try again.")
        sys.exit(1)

    # Step 5: Initialize embedding provider
    from verse_sdk.embeddings.generate_embeddings import initialize_provider
    print(f"Initializing embedding provider '{args.provider}'...")
    embed_fn, client, config = initialize_provider(args.provider)
    print()

    # Step 6: Embed episodes
    print(f"Embedding {len(episodes)} episodes...")
    episode_embeddings = embed_episodes(episodes, embed_fn, client, config)
    print(f"  Embedded {len(episode_embeddings)} episodes")
    print()

    # Step 7: Write puranic-index/<key>.yml
    index_dir = args.project_dir / "data" / "puranic-index"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_file = index_dir / f"{key}.yml"

    with open(index_file, "w", encoding="utf-8") as f:
        yaml.dump(episodes, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"Wrote episode index: {index_file}")

    # Step 8: Write embeddings/<key>.json
    embeddings_dir = args.project_dir / "data" / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    embeddings_file = embeddings_dir / f"{key}.json"

    embeddings_output = {
        "key": key,
        "model": config["model"],
        "generated_at": datetime.now().isoformat(),
        "episodes": episode_embeddings,
    }
    with open(embeddings_file, "w", encoding="utf-8") as f:
        json.dump(embeddings_output, f, ensure_ascii=False, indent=2)
    print(f"Wrote embeddings    : {embeddings_file}")

    # Step 9: Update puranic-references.yml
    refs = load_puranic_references(args.project_dir)
    refs[key] = {
        "enabled": True,
        "name": key.replace("-", " ").title(),
        "format": source_file.suffix.lstrip("."),
    }
    save_puranic_references(refs, args.project_dir)
    ref_file = args.project_dir / "data" / "puranic-references.yml"
    print(f"Updated references  : {ref_file}")

    print()
    print("=" * 60)
    print("INDEXING COMPLETE")
    print("=" * 60)
    print(f"  Episodes indexed : {len(episodes)}")
    print(f"  Episodes embedded: {len(episode_embeddings)}")
    print()


if __name__ == "__main__":
    main()
