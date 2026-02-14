# Publishing to PyPI

This guide walks through publishing `verse-sdk` to the Python Package Index (PyPI).

## Prerequisites

### 1. Install Build Tools

```bash
pip install --upgrade pip build twine
```

### 2. Create PyPI Accounts

You'll need accounts on both TestPyPI (for testing) and PyPI (for production):

- **TestPyPI**: https://test.pypi.org/account/register/
- **PyPI**: https://pypi.org/account/register/

For both:
1. Register an account
2. Verify your email
3. Enable 2FA (required)

### 3. Create API Tokens

API tokens are more secure than passwords and recommended for publishing.

#### TestPyPI Token

1. Go to https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Name it (e.g., "verse-sdk-upload")
4. Scope: "Entire account" (initially, then narrow to project after first upload)
5. Save the token (starts with `pypi-`)

#### PyPI Token

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name it (e.g., "verse-sdk-upload")
4. Scope: "Entire account" (initially, then narrow to project after first upload)
5. Save the token (starts with `pypi-`)

### 4. Configure PyPI Credentials

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...your-real-pypi-token...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZwI...your-test-pypi-token...
```

**Security Note**: Protect this file:
```bash
chmod 600 ~/.pypirc
```

### 5. Managing Published Projects

After publishing, manage your projects at:

- **PyPI Projects**: https://pypi.org/manage/projects/
- **TestPyPI Projects**: https://test.pypi.org/manage/projects/

From there you can:
- View package statistics and downloads
- Manage project maintainers and collaborators
- Create project-specific API tokens (recommended after first upload)
- Update package description and metadata
- Delete releases (use with caution!)

## Pre-Publishing Checklist

Before each release, ensure:

### 1. Update Version Number

Edit `setup.py` and increment the version:

```python
version="0.1.0",  # Update this
```

Follow [Semantic Versioning](https://semver.org/):
- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backwards compatible
- **Patch** (0.0.1): Bug fixes

### 2. Update README

- Ensure all examples work
- Update any changed command syntax
- Check links are valid

### 3. Add Author Email (Optional)

Edit `setup.py`:

```python
author_email="your-email@example.com",
```

### 4. Create/Update CHANGELOG.md

Document what changed in this version:

```markdown
## [0.1.0] - 2026-02-01

### Added
- Initial release
- verse-generate command with --all flag
- Support for chapter-based and non-chapter texts

### Fixed
- Bug fixes here

### Changed
- Breaking changes here
```

### 5. Test Locally

```bash
# Install in editable mode
pip install -e .

# Test all commands
verse-generate --help
verse-generate --chapter 1 --verse 1 --all
```

### 6. Clean Previous Builds

```bash
rm -rf dist/ build/ verse_sdk.egg-info/
```

## Publishing Process

### Step 1: Build Distribution Packages

```bash
python -m build
```

This creates:
- `dist/verse-sdk-0.1.0-py3-none-any.whl` (wheel format)
- `dist/verse-sdk-0.1.0.tar.gz` (source distribution)

### Step 2: Test on TestPyPI

Upload to TestPyPI first to catch any issues:

```bash
python -m twine upload --repository testpypi dist/*
```

You'll see output like:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading verse-sdk-0.1.0-py3-none-any.whl
Uploading verse-sdk-0.1.0.tar.gz
```

View your package: https://test.pypi.org/project/verse-sdk/

### Step 3: Test Installation from TestPyPI

In a new virtual environment:

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI (with real PyPI for dependencies)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ verse-sdk

# Test the installation
verse-generate --help

# Clean up
deactivate
rm -rf test_env
```

### Step 4: Upload to Real PyPI

If testing looks good, upload to production PyPI:

```bash
python -m twine upload dist/*
```

View your package: https://pypi.org/project/verse-sdk/

### Step 5: Verify Production Installation

```bash
# In a new environment
pip install verse-sdk

# Test it works
verse-generate --help
```

### Step 6: Tag the Release in Git

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### Step 7: Create GitHub Release

1. Go to https://github.com/sanatan-learnings/verse-sdk/releases
2. Click "Draft a new release"
3. Select the tag you just created
4. Title: "v0.1.0"
5. Description: Copy from CHANGELOG.md
6. Attach the dist files (optional)
7. Publish release

### Step 8: Manage Your Published Package

After publishing, you can manage your package at:

**Production PyPI:**
- View package: https://pypi.org/project/verse-sdk/
- Manage project: https://pypi.org/manage/projects/

**TestPyPI:**
- View package: https://test.pypi.org/project/verse-sdk/
- Manage project: https://test.pypi.org/manage/projects/

From the management page you can:
- ✅ View download statistics
- ✅ Add/remove maintainers
- ✅ Create project-specific API tokens (recommended!)
- ✅ Update package metadata
- ✅ Manage releases

**Recommended:** After first upload, create a project-specific token instead of using an account-wide token for better security.

## Quick Release Script

An automated publish script is available at `scripts/publish.sh`.

### Usage

```bash
# Run from project root
./scripts/publish.sh
```

The script will guide you through:
1. Optionally updating the version number
2. Cleaning old builds
3. Building distribution packages
4. Uploading to TestPyPI for testing (optional)
5. Uploading to production PyPI (with confirmation)
6. Creating and pushing git tags (optional)

### Features

- ✅ Version validation and updating
- ✅ Automatic build cleaning
- ✅ TestPyPI upload for testing
- ✅ Safety confirmations before production upload
- ✅ Git tagging automation
- ✅ Color-coded output
- ✅ Error handling

## Troubleshooting

### "The user '<username>' isn't allowed to upload to project"

This means the project name is already taken. Either:
- Choose a different name in `setup.py`
- Contact the current owner if it's an abandoned project
- Use a namespace (e.g., `my-verse-sdk`)

### "File already exists"

You're trying to upload the same version again. PyPI doesn't allow overwriting versions.

Solution: Increment the version number in `setup.py`

### "Invalid distribution file"

The build failed or produced corrupt files.

Solution:
```bash
rm -rf dist/ build/ *.egg-info/
python -m build
```

### Import Error After Installation

Common causes:
- Package name vs. import name mismatch
- Missing dependencies in `install_requires`
- Entry points not configured correctly

Check `setup.py`:
- `name` should match pip install name
- `packages=find_packages()` should find your modules
- `entry_points` should reference correct module paths

### Testing Locally Before Publishing

```bash
# Install in editable mode
pip install -e .

# Or create a wheel and install it
python -m build
pip install dist/verse-sdk-*.whl
```

## Updating After Initial Release

For subsequent releases:

1. Make your changes
2. Update version in `setup.py`
3. Update `CHANGELOG.md`
4. Clean, build, and upload:

```bash
rm -rf dist/ build/ *.egg-info/
python -m build
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*  # Then production
```

5. Tag in git:
```bash
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1
```

## Automation with GitHub Actions

For automatic publishing on git tags, create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI token to GitHub secrets:
1. Go to repository Settings → Secrets → Actions
2. Add secret: `PYPI_API_TOKEN`
3. Paste your PyPI token

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [TestPyPI](https://test.pypi.org/)
