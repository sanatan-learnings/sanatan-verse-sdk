# verse-index-sources

Index Puranic source texts (PDFs, TXTs, MDs) into structured episodes and embeddings for RAG retrieval.

## Synopsis

```bash
verse-index-sources --file PATH [OPTIONS]
```

## Description

`verse-index-sources` processes a source document, extracts structured Puranic episodes using GPT-4o, embeds them with Amazon Bedrock Cohere, and writes the results to the project's data directory. The indexed episodes are later used by `verse-puranic-context` for retrieval-augmented generation (RAG) when generating context boxes.

**Pipeline:**
1. Extract raw text from the source file (PDF/TXT/MD)
2. Chunk text into ~1500-character segments
3. Use GPT-4o to extract structured episodes (id, type, keywords, summaries in English and Hindi)
4. Deduplicate episodes by ID
5. Embed each episode using the chosen embedding provider
6. Write episode index to `data/puranic-index/<key>.yml`
7. Write embeddings to `data/embeddings/<key>.json`
8. Register the source in `data/puranic-references.yml`

## Options

### Required

- `--file PATH` - Path to source file (`.pdf`, `.txt`, or `.md`)

### Optional

- `--force` - Re-index even if this source has already been indexed
- `--provider {bedrock-cohere,openai}` - Embedding provider (default: `bedrock-cohere`)
- `--project-dir PATH` - Project directory (default: current directory)

## Examples

```bash
# Index a PDF source
verse-index-sources --file data/sources/valmiki-ramayana.pdf

# Index a text file, force re-index
verse-index-sources --file data/sources/devi-bhagavata.txt --force

# Use OpenAI embeddings instead of Bedrock Cohere
verse-index-sources --file data/sources/notes.md --provider openai
```

## Output Files

### Episode Index

`data/puranic-index/<key>.yml` — one YAML list of all extracted episodes:

```yaml
- id: rama-exile-episode
  type: story
  keywords:
    - Rama
    - exile
    - forest
  source:
    book: Valmiki Ramayana
    sarga: Ayodhya Kanda, Sarga 20
  summary_en: "Rama accepts exile to honor his father Dasharatha's promise..."
  summary_hi: "राम ने अपने पिता दशरथ के वचन का सम्मान करते हुए वनवास स्वीकार किया..."
```

### Embeddings

`data/embeddings/<key>.json`:

```json
{
  "key": "valmiki-ramayana",
  "model": "cohere.embed-multilingual-v3",
  "generated_at": "2024-01-15T10:30:00",
  "episodes": [
    {"id": "rama-exile-episode", "embedding": [0.12, -0.34, ...]}
  ]
}
```

### References Registry

`data/puranic-references.yml` — tracks all indexed sources:

```yaml
valmiki-ramayana:
  enabled: true
  name: Valmiki Ramayana
  format: pdf
```

## Requirements

- `OPENAI_API_KEY` environment variable (for GPT-4o episode extraction)
- AWS credentials configured (for `bedrock-cohere` provider)
- `pdfplumber` installed for PDF sources (`pip install pdfplumber`)

## Workflow

```bash
# 1. Place source documents in data/sources/
mkdir -p data/sources
cp /path/to/valmiki-ramayana.pdf data/sources/

# 2. Index the source
verse-index-sources --file data/sources/valmiki-ramayana.pdf

# 3. Generate Puranic context for verses (RAG-grounded)
verse-puranic-context --collection hanuman-chalisa --all
```

## See Also

- [verse-puranic-context](verse-puranic-context.md) - Generate Puranic context boxes using indexed sources
