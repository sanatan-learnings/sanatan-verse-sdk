# Agent Instructions

This file contains instructions for AI agents (like Claude Code) working on this project.

## Publishing to PyPI

When the user asks to publish to PyPI, follow these steps:

### 1. Pre-requisites
- Ensure all changes are committed and pushed to GitHub
- Version should already be bumped in `setup.py`
- User should have PyPI credentials configured (twine will use them)

### 2. Publishing Process

The `scripts/publish.sh` script now supports both interactive and automated modes.

#### Automated Mode (Recommended for Agents)

For typical releases (use current version, skip TestPyPI, auto-approve):
```bash
bash scripts/publish.sh --yes --skip-testpypi
```

For releases with version bump:
```bash
bash scripts/publish.sh --version 0.25.0 --yes --skip-testpypi
```

#### CLI Options

- `--yes` / `-y` - Auto-approve all prompts (skip TestPyPI, approve PyPI, create tag)
- `--skip-testpypi` - Skip TestPyPI upload
- `--no-tag` - Don't create git tag after publishing
- `--version X.Y.Z` - Set specific version (skips version prompt)
- `--help` / `-h` - Show help message

#### Interactive Mode (Legacy)

Run without arguments to use interactive prompts:
```bash
bash scripts/publish.sh
```

### 3. Typical Answers (Interactive Mode Only)

When running in interactive mode, use these typical answers:

1. **"Do you want to update the version?"**
   - Answer: **No** (version should already be updated in setup.py before publishing)

2. **"Upload to TestPyPI first for testing?"**
   - Answer: **No, skip TestPyPI** (for minor releases and bug fixes)
   - Answer: **Yes, test first** (for major releases or significant changes)

3. **"Proceed with uploading to PRODUCTION PyPI?"**
   - Answer: **Yes, publish to PyPI** (after confirming with user)

4. **"Create git tag and push?"**
   - Answer: **Yes, create tag** (this is standard practice)

### 4. Post-Publishing

After successful publish:
- Provide the user with the PyPI package link
- Provide the GitHub releases link for creating a release
- Confirm the installation command: `pip install sanatan-sdk`

### Example Workflows

#### Automated Publishing (Recommended)
```bash
# 1. User requests: "publish to PyPI"

# 2. Agent runs automated publish script:
bash scripts/publish.sh --yes --skip-testpypi

# 3. Script automatically:
#    - Uses current version from setup.py
#    - Cleans old builds
#    - Builds package
#    - Uploads to PyPI
#    - Creates and pushes git tag

# 4. Agent provides links and confirmation
```

#### Manual Steps (If Script Unavailable)
```bash
# 1. Clean and build
rm -rf dist/ build/ verse_sdk.egg-info/ sanatan_sdk.egg-info/
python -m build

# 2. Upload to PyPI
python -m twine upload dist/*

# 3. Create git tag
git tag -a "vX.Y.Z" -m "Release version X.Y.Z"
git push origin vX.Y.Z

# 4. Provide confirmation
```

## Version Bumping

**IMPORTANT**: Do NOT update the version in `setup.py` during development or in regular commits. The version should ONLY be bumped right before publishing to PyPI.

### When to Bump Version

Only update `setup.py` version when:
1. User explicitly asks to publish to PyPI
2. Running the publish script (`scripts/publish.sh`)
3. As part of the release commit (just before tagging)

### Version Guidelines

- **Patch release** (0.23.0 → 0.23.1): Bug fixes, documentation updates
- **Minor release** (0.23.0 → 0.24.0): New features, non-breaking changes
- **Major release** (0.23.0 → 1.0.0): Breaking changes

### Workflow

```bash
# 1. Make changes and commit (WITHOUT version bump)
git add .
git commit -m "feat: Add new feature"
git push

# 2. When ready to publish, use publish script (it can update version)
bash scripts/publish.sh --version 0.25.0 --yes --skip-testpypi

# OR update version manually right before publishing
# Edit setup.py to set version="0.25.0"
git add setup.py
git commit -m "chore: Bump version to 0.25.0"
bash scripts/publish.sh --yes --skip-testpypi
```

## Commit Message Format

Follow the existing commit message format:

```
<type>: <description> (vX.Y.Z)

- Detailed change 1
- Detailed change 2
- Detailed change 3

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `BREAKING CHANGE`

## Testing

Before publishing:
1. Ensure local tests pass (if any)
2. Check that documentation is updated
3. Verify all changed files are committed
4. For major changes, consider testing via TestPyPI first

## Project Structure Notes

- **Scene descriptions**: Located in `data/scenes/` (YAML format)
- **Themes**: Located in `data/themes/<collection>/`
- **Verse files**: Located in `_verses/<collection>/` (use dash format: `verse-01.md`)
- **Canonical text**: Located in `data/verses/<collection>.yaml`

## Common Operations

### Adding a new collection
1. Add entry to `_data/collections.yml`
2. Create directory: `_verses/<collection>/`
3. Create theme: `data/themes/<collection>/modern-minimalist.yml`
4. Create scenes: `data/scenes/<collection>.yml`
5. Create canonical text: `data/verses/<collection>.yaml`

### Updating documentation
When changing file paths or structure, update all references in:
- `docs/commands/*.md`
- `docs/usage.md`
- `docs/development.md`
- `docs/troubleshooting.md`
- `verse_sdk/cli/*.py` (help text)
