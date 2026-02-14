"""Embedding generation modules."""

# Import main generate_embeddings function (supports OpenAI and local)
import sys
from pathlib import Path

def generate_embeddings(
    verses_dir: Path,
    output_file: Path,
    provider: str = 'openai'
):
    """
    Generate embeddings for verses using OpenAI or local models.

    Args:
        verses_dir: Directory containing verse markdown files
        output_file: Path to output JSON file
        provider: 'openai' (default) or 'huggingface' (local)
    """
    # Import here to avoid circular imports
    from . import generate_embeddings as gen_module

    # Temporarily override sys.argv to pass arguments to the script
    old_argv = sys.argv
    sys.argv = [
        'generate_embeddings',
        '--provider', provider,
        '--verses-dir', str(verses_dir),
        '--output', str(output_file)
    ]

    try:
        gen_module.main()
    finally:
        sys.argv = old_argv

__all__ = [
    "generate_embeddings",
]
