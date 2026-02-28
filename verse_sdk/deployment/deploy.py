#!/usr/bin/env python3
"""
Wrapper to run the deployment shell script.
"""

import subprocess
import sys
from pathlib import Path


def _print_help():
    print(
        "Usage: verse-deploy\n"
        "\n"
        "Deploy Cloudflare Workers as an OpenAI API proxy for verse-based projects.\n"
        "\n"
        "Options:\n"
        "  --status    Show current worker status and exit\n"
        "  --dry-run   Validate prerequisites and print planned actions\n"
        "  -h, --help  Show this help message and exit\n"
    )


def main():
    """Run the Cloudflare Worker deployment script."""
    if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
        _print_help()
        sys.exit(0)

    script_path = Path(__file__).parent / "deploy-cloudflare-worker.sh"

    if not script_path.exists():
        print(f"Error: Deployment script not found at {script_path}")
        sys.exit(1)

    # Run the shell script
    result = subprocess.run([str(script_path), *sys.argv[1:]], cwd=Path.cwd())
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
