# verse-puranic-context

Generate Puranic context boxes for verse files using RAG retrieval or GPT-4o free recall.

## Synopsis

```bash
verse-puranic-context --collection COLLECTION (--verse ID | --all) [OPTIONS]
```

## Description

`verse-puranic-context` uses AI to identify relevant Puranic references (stories, characters, concepts, etymologies) and injects a `puranic_context` block into each verse file's frontmatter.

**RAG mode (recommended):** When indexed sources are available (`data/puranic-references.yml` + `data/puranic-index/`), the command embeds the verse text, retrieves the most relevant Puranic episodes via cosine similarity, and provides them as grounding context to GPT-4o.

**Free-recall fallback:** If no sources are indexed, the command prompts you to continue with GPT-4o's built-in knowledge. Use `verse-index-sources` to add indexed sources and switch to RAG mode.

## Options

### Required

- `--collection KEY` - Collection key (e.g., `hanuman-chalisa`, `sundar-kaand`)
- `--verse ID` or `--all` - Process a specific verse ID, or all verses in the collection (mutually exclusive)

### Optional

- `--regenerate` - Overwrite existing `puranic_context` entries (default: skip verses that already have context)
- `--subject NAME` - Filter retrieved episodes to those involving this subject (e.g. `Hanuman`). See [Subject Filtering](#subject-filtering) below.
- `--subject-type TYPE` - Type label for the subject used in the GPT-4o prompt (default: `deity`)
- `--project-dir PATH` - Project directory (default: current directory)

## Examples

```bash
# Generate for a specific verse
verse-puranic-context --collection hanuman-chalisa --verse chaupai-15

# Generate for all verses missing context
verse-puranic-context --collection bajrang-baan --all

# Force regenerate even if context exists
verse-puranic-context --collection hanuman-chalisa --verse chaupai-18 --regenerate

# Regenerate all verses in a collection
verse-puranic-context --collection sundar-kaand --all --regenerate

# Filter context to a specific deity (reduces cross-deity noise)
verse-puranic-context --collection hanuman-chalisa --all --subject Hanuman

# With an explicit subject type
verse-puranic-context --collection hanuman-chalisa --all --subject Hanuman --subject-type deity
```

## Subject Filtering

When indexing a broad source like Shiv Puran, RAG retrieval can surface episodes about Parvati, Shiva, or Nandi for verses that are specifically about Hanuman. Use `--subject` to keep context relevant.

```bash
verse-puranic-context --collection hanuman-chalisa --all --subject Hanuman
```

**What it does in two layers:**

1. **Pre-filter (keyword):** After RAG retrieval, drops episodes where the subject name does not appear in the episode's keywords, id, or summary. For example, a Parvati appearance story will be dropped for `--subject Hanuman`.

2. **Prompt constraint (LLM):** Instructs GPT-4o to only generate `puranic_context` entries where the subject is a direct participant, catching cases the keyword filter misses.

**Fallback:** If the keyword filter removes all retrieved episodes (e.g. the subject name is not explicitly mentioned in the indexed text), it falls back to the full retrieved set so generation still runs with the prompt constraint applied.

**`--subject-type`** provides a label for the prompt (default: `deity`). Use other values for non-deity subjects:

```bash
verse-puranic-context --collection upanishads --all --subject Brahman --subject-type concept
verse-puranic-context --collection ramayana --all --subject Rama --subject-type avatar
```

## Output

Each processed verse file gets a `puranic_context` block added to its YAML frontmatter:

```yaml
puranic_context:
  - id: hanuman-leaping-ocean
    type: story
    priority: high
    title:
      en: Hanuman's Leap Across the Ocean
      hi: हनुमान का समुद्र लांघना
    icon: 🌊
    story_summary:
      en: "Hanuman leaps across the ocean to Lanka in search of Sita..."
      hi: "हनुमान सीता की खोज में समुद्र लांघकर लंका पहुंचते हैं..."
    theological_significance:
      en: "Symbolises the power of devotion to overcome all obstacles..."
      hi: "भक्ति की शक्ति से सभी बाधाओं पर विजय का प्रतीक..."
    practical_application:
      en: "Chanting this verse invokes Hanuman's strength in times of difficulty..."
      hi: "इस चौपाई का पाठ कठिन समय में हनुमान की शक्ति का आह्वान करता है..."
    source_texts:
      - text: Shiv Puran
        section: Part 1
    related_verses: []
```

### Context Entry Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique kebab-case slug |
| `type` | enum | `story`, `concept`, `character`, `etymology`, `practice`, `cross_reference` |
| `priority` | enum | `high`, `medium`, `low` |
| `title.en` / `title.hi` | string | English and Hindi title |
| `icon` | string | Single emoji |
| `story_summary` | object | 2-4 sentence summary (en + hi) |
| `theological_significance` | object | Spiritual meaning (en + hi) |
| `practical_application` | object | Practical use (en + hi) |
| `source_texts` | list | Indexed sources only (constrained to avoid hallucination) |
| `related_verses` | list | Cross-references to other verses |

## RAG Workflow

```bash
# 1. Index source texts first
verse-index-sources --file data/sources/shiv-puran-part1.txt

# 2. Generate context filtered to the collection's primary deity
verse-puranic-context --collection hanuman-chalisa --all --subject Hanuman
```

Each verse is embedded using the same provider as the indexed source (detected from `_meta.embedding_provider`) and matched against indexed episodes to select the top-8 most relevant passages as grounding context.

## Requirements

- `OPENAI_API_KEY` environment variable
- Verse files in `_verses/<collection>/<verse-id>.md` with YAML frontmatter
- AWS credentials only if using `bedrock-cohere` indexed sources

## See Also

- [verse-index-sources](verse-index-sources.md) - Index Puranic source texts for RAG retrieval
- [verse-generate](verse-generate.md) - Generate full verse content (translation, images, audio, embeddings)
