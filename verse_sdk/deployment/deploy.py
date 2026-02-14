#!/usr/bin/env python3
"""
Wrapper to run the deployment shell script.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run the Cloudflare Worker deployment script."""
    script_path = Path(__file__).parent / "deploy-cloudflare-worker.sh"

    if not script_path.exists():
        print(f"Error: Deployment script not found at {script_path}")
        sys.exit(1)

    # Run the shell script
    result = subprocess.run([str(script_path)], cwd=Path.cwd())
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
