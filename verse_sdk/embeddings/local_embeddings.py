"""Local embedding generation using sentence-transformers."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed")
    print("Please install it with: pip install sentence-transformers")
    sys.exit(1)

from ..utils import yaml_parser, file_utils


class LocalEmbeddingGenerator:
    """Generate embeddings locally using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimensions: int = 384
    ):
        """
        Initialize the local embedding generator.

        Args:
            model_name: HuggingFace model name
            dimensions: Expected embedding dimensions
        """
        self.model_name = model_name
        self.dimensions = dimensions
        self.model = None

    def load_model(self) -> None:
        """Load the sentence transformer model."""
        if self.model is None:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded successfully!")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        if self.model is None:
            self.load_model()

        return self.model.encode(text).tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        if self.model is None:
            self.load_model()

        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]

    def process_verse_files(
        self,
        verses_dir: Path,
        document_builder: Callable[[Dict[str, Any], str], str],
        url_generator: Optional[Callable[[Dict[str, Any]], str]] = None,
        languages: List[str] = ["en", "hi"],
        file_pattern: str = "*.md"
    ) -> Dict[str, Any]:
        """
        Process verse files and generate embeddings.

        Args:
            verses_dir: Directory containing verse markdown files
            document_builder: Function to build document text from verse data
            url_generator: Optional function to generate verse URL
            languages: List of language codes to process
            file_pattern: Glob pattern for finding verse files

        Returns:
            Dictionary containing embeddings and metadata
        """
        if not verses_dir.exists():
            raise ValueError(f"Verses directory not found: {verses_dir}")

        self.load_model()

        verse_files = file_utils.find_markdown_files(verses_dir, file_pattern)
        print(f"Found {len(verse_files)} verse files\n")

        # Collect results for each language
        results = {lang: [] for lang in languages}

        for verse_file in verse_files:
            print(f"Processing {verse_file.name}...")

            verse_data = yaml_parser.extract_yaml_frontmatter(verse_file)
            if not verse_data:
                print(f"  Warning: Could not extract YAML from {verse_file.name}")
                continue

            verse_num = verse_data.get('verse_number', 0)

            # Process each language
            for lang in languages:
                # Build document using provided function
                doc = document_builder(verse_data, lang)

                # Generate embedding
                embedding = self.generate_embedding(doc)

                # Build result
                result = {
                    'verse_number': verse_num,
                    'title': verse_data.get(f'title_{lang}', ''),
                    'embedding': embedding,
                }

                # Add URL if generator provided
                if url_generator:
                    result['url'] = url_generator(verse_data)

                # Add metadata
                result['metadata'] = {
                    'devanagari': verse_data.get('devanagari', ''),
                    'transliteration': verse_data.get('transliteration', ''),
                }

                # Add language-specific metadata if available
                lit_trans = yaml_parser.get_nested_value(
                    verse_data, 'literal_translation', lang, ''
                )
                if lit_trans:
                    result['metadata']['literal_translation'] = lit_trans

                results[lang].append(result)

            print()

        # Sort by verse number
        for lang in languages:
            results[lang].sort(
                key=lambda v: int(v['verse_number'])
                if isinstance(v['verse_number'], (int, str))
                and str(v['verse_number']).isdigit()
                else 999
            )

        return {
            'model': self.model_name,
            'dimensions': self.dimensions,
            'provider': 'local',
            'generated_at': datetime.now().isoformat(),
            'verses': results
        }

    def save_embeddings(
        self,
        verses_dir: Path,
        output_file: Path,
        document_builder: Callable[[Dict[str, Any], str], str],
        url_generator: Optional[Callable[[Dict[str, Any]], str]] = None,
        languages: List[str] = ["en", "hi"]
    ) -> None:
        """
        Generate and save embeddings to a file.

        Args:
            verses_dir: Directory containing verse markdown files
            output_file: Path to output JSON file
            document_builder: Function to build document text from verse data
            url_generator: Optional function to generate verse URL
            languages: List of language codes to process
        """
        print("=" * 60)
        print("Verse Embeddings Generator (Local)")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Dimensions: {self.dimensions}")
        print(f"Languages: {', '.join(languages)}")
        print(f"Verses directory: {verses_dir}")
        print(f"Output file: {output_file}")
        print()

        # Generate embeddings
        results = self.process_verse_files(
            verses_dir,
            document_builder,
            url_generator,
            languages
        )

        # Write to file
        print(f"Writing embeddings to {output_file}...")
        file_utils.write_json(results, output_file)

        # Print summary
        print()
        print("=" * 60)
        print("Generation Complete!")
        print("=" * 60)
        total_verses = len(results['verses'][languages[0]])
        print(f"Total verses processed: {total_verses}")
        for lang in languages:
            print(f"{lang.upper()} embeddings: {len(results['verses'][lang])}")
        print(f"Output file size: {file_utils.get_file_size_kb(output_file):.1f} KB")
        print(f"Cost: FREE (generated locally)")
        print()
