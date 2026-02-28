# Embeddings Config

Use `_data/embeddings.yml` to set project-wide defaults for embedding providers, models, and output paths. CLI flags always win, then config, then environment variables, then SDK defaults.

## Example

```yaml
active_provider: openai
active_model: text-embedding-3-small
output_dir: data/embeddings/collections
index_path: data/embeddings/collections/index.json
puranic_embeddings_dir: data/embeddings/puranic
max_input_chars: 2048
truncate_policy: chunk
#
# Hugging Face example:
# active_provider: huggingface
# active_model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

## Precedence

1. CLI flags (highest)
2. `_data/embeddings.yml`
3. Environment variables
4. SDK defaults (lowest)

CLI overrides are logged, for example:

`Using provider=bedrock-cohere from CLI flag (overrides config: openai).`

## Environment Variables

- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDINGS_OUTPUT_DIR`
- `EMBEDDINGS_INDEX_PATH`
- `EMBEDDINGS_MAX_INPUT_CHARS`
- `EMBEDDINGS_TRUNCATE_POLICY`
- `PURANIC_EMBEDDINGS_DIR`

## Supported Commands

- `verse-embeddings` (provider/model/output/index)
- `verse-index-sources` (provider + puranic embeddings dir)
- `verse-puranic-context` (puranic embeddings dir)
