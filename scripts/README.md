# Publishing Scripts

This directory contains scripts for publishing and maintaining the verse-content-sdk package.

## publish.sh

Automated script for publishing to PyPI.

### Usage

```bash
# Run from project root
./scripts/publish.sh
```

### What it does

1. Checks and installs required tools (build, twine)
2. Shows current version and optionally updates it
3. Cleans old builds
4. Builds distribution packages
5. Uploads to TestPyPI for testing (optional)
6. Uploads to production PyPI (requires confirmation)
7. Creates and pushes git tags (optional)

### Prerequisites

- PyPI credentials configured in `~/.pypirc`
- See [Publishing Documentation](../docs/publishing.md) for setup instructions

### First Time Setup

1. Create PyPI and TestPyPI accounts
2. Generate API tokens
3. Configure `~/.pypirc` with tokens
4. Run `./scripts/publish.sh`

For detailed instructions, see [Publishing Documentation](../docs/publishing.md).
