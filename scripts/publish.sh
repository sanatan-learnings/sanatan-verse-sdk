#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command-line arguments
AUTO_APPROVE=false
SKIP_TESTPYPI=false
NO_TAG=false
NEW_VERSION=""

show_help() {
    cat << EOF
PyPI Publishing Script for sanatan-verse-sdk

Usage: $0 [OPTIONS]

Options:
  -y, --yes              Auto-approve all prompts (skip TestPyPI, approve PyPI, create tag)
  --skip-testpypi        Skip TestPyPI upload
  --no-tag               Don't create git tag after publishing
  --version VERSION      Set version (e.g., --version 0.24.1)
  -h, --help             Show this help message

Examples:
  # Interactive mode (default)
  $0

  # Fully automated (use current version, skip TestPyPI, auto-approve, create tag)
  $0 --yes --skip-testpypi

  # Set version and auto-approve
  $0 --version 0.25.0 --yes

  # Skip TestPyPI and git tag
  $0 --skip-testpypi --no-tag

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes)
            AUTO_APPROVE=true
            shift
            ;;
        --skip-testpypi)
            SKIP_TESTPYPI=true
            shift
            ;;
        --no-tag)
            NO_TAG=true
            shift
            ;;
        --version)
            NEW_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}  PyPI Publishing Script${NC}"
echo -e "${BLUE}  sanatan-verse-sdk${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo -e "${RED}Error: setup.py not found. Run this script from the project root.${NC}"
    exit 1
fi

# Check if required tools are installed
echo -e "${YELLOW}Checking required tools...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: python not found. Please install Python.${NC}"
    exit 1
fi

if ! python -c "import build" 2>/dev/null; then
    echo -e "${YELLOW}Installing build package...${NC}"
    pip install build
fi

if ! python -c "import twine" 2>/dev/null; then
    echo -e "${YELLOW}Installing twine package...${NC}"
    pip install twine
fi

echo -e "${GREEN}✓ All required tools installed${NC}"
echo ""

# Show current version
CURRENT_VERSION=$(grep "version=" setup.py | head -1 | sed -E 's/.*version="([^"]+)".*/\1/')
echo -e "${BLUE}Current version: ${GREEN}${CURRENT_VERSION}${NC}"
echo ""

# Handle version update
if [ -n "$NEW_VERSION" ]; then
    # Validate version format
    if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}Error: Invalid version format. Use X.Y.Z (e.g., 0.1.1)${NC}"
        exit 1
    fi

    # Update version in setup.py
    sed -i.bak "s/version=\"$CURRENT_VERSION\"/version=\"$NEW_VERSION\"/" setup.py
    rm setup.py.bak

    echo -e "${GREEN}✓ Version updated to ${NEW_VERSION}${NC}"
    VERSION=$NEW_VERSION
elif [ "$AUTO_APPROVE" = false ]; then
    # Interactive mode: ask if user wants to update version
    read -p "Do you want to update the version? (y/n): " UPDATE_VERSION

    if [ "$UPDATE_VERSION" = "y" ] || [ "$UPDATE_VERSION" = "Y" ]; then
        read -p "Enter new version (e.g., 0.1.1): " NEW_VERSION

        # Validate version format
        if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "${RED}Error: Invalid version format. Use X.Y.Z (e.g., 0.1.1)${NC}"
            exit 1
        fi

        # Update version in setup.py
        sed -i.bak "s/version=\"$CURRENT_VERSION\"/version=\"$NEW_VERSION\"/" setup.py
        rm setup.py.bak

        echo -e "${GREEN}✓ Version updated to ${NEW_VERSION}${NC}"
        VERSION=$NEW_VERSION
    else
        VERSION=$CURRENT_VERSION
    fi
else
    # Auto-approve mode: use current version
    VERSION=$CURRENT_VERSION
fi

echo ""
echo -e "${YELLOW}Publishing version: ${GREEN}${VERSION}${NC}"
echo ""

# Clean old builds
echo -e "${YELLOW}Cleaning old builds...${NC}"
rm -rf dist/ build/ verse_sdk.egg-info/ sanatan_sdk.egg-info/
echo -e "${GREEN}✓ Old builds cleaned${NC}"
echo ""

# Build the package
echo -e "${YELLOW}Building package...${NC}"
python -m build
echo -e "${GREEN}✓ Package built successfully${NC}"
echo ""

# Show what was built
echo -e "${BLUE}Built files:${NC}"
ls -lh dist/
echo ""

# Handle TestPyPI upload
if [ "$SKIP_TESTPYPI" = false ]; then
    if [ "$AUTO_APPROVE" = false ]; then
        # Interactive mode: ask about TestPyPI
        read -p "Upload to TestPyPI first for testing? (recommended, y/n): " TEST_UPLOAD
    else
        # Auto-approve mode: skip TestPyPI
        TEST_UPLOAD="n"
    fi

    if [ "$TEST_UPLOAD" = "y" ] || [ "$TEST_UPLOAD" = "Y" ]; then
        echo ""
        echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
        python -m twine upload --repository testpypi dist/*

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Successfully uploaded to TestPyPI${NC}"
            echo ""
            echo -e "${BLUE}View your package at:${NC}"
            echo -e "https://test.pypi.org/project/sanatan-verse-sdk/${VERSION}/"
            echo ""
            echo -e "${YELLOW}Test installation with:${NC}"
            echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sanatan-verse-sdk"
            echo ""
        else
            echo -e "${RED}Error uploading to TestPyPI. Check the error above.${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}Skipping TestPyPI upload (--skip-testpypi flag)${NC}"
    echo ""
fi

# Confirm before uploading to production PyPI
if [ "$AUTO_APPROVE" = false ]; then
    echo ""
    echo -e "${RED}⚠️  WARNING: You are about to upload to PRODUCTION PyPI${NC}"
    echo -e "${RED}This action cannot be undone!${NC}"
    echo ""
    read -p "Are you sure you want to continue? (y/yes): " CONFIRM

    if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${YELLOW}Upload cancelled.${NC}"
        exit 0
    fi
else
    echo ""
    echo -e "${YELLOW}Auto-approving PyPI upload (--yes flag)${NC}"
fi

# Upload to PyPI
echo ""
echo -e "${YELLOW}Uploading to PyPI...${NC}"
python -m twine upload dist/*

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}===========================================${NC}"
    echo -e "${GREEN}✓ Successfully published to PyPI!${NC}"
    echo -e "${GREEN}===========================================${NC}"
    echo ""
    echo -e "${BLUE}View your package at:${NC}"
    echo -e "https://pypi.org/project/sanatan-verse-sdk/${VERSION}/"
    echo ""
    echo -e "${BLUE}Install with:${NC}"
    echo "pip install sanatan-verse-sdk"
    echo ""

    # Handle git tagging
    if [ "$NO_TAG" = false ]; then
        if [ "$AUTO_APPROVE" = false ]; then
            # Interactive mode: ask about tagging
            read -p "Create git tag and push? (y/n): " CREATE_TAG
        else
            # Auto-approve mode: create tag
            CREATE_TAG="y"
        fi

        if [ "$CREATE_TAG" = "y" ] || [ "$CREATE_TAG" = "Y" ]; then
            git add setup.py
            git commit -m "Bump version to ${VERSION}" || true
            git tag -a "v${VERSION}" -m "Release version ${VERSION}"
            git push origin main
            git push origin "v${VERSION}"

            echo -e "${GREEN}✓ Git tag created and pushed${NC}"
            echo ""
            echo -e "${BLUE}Create GitHub release at:${NC}"
            echo "https://github.com/sanatan-learnings/sanatan-verse-sdk/releases/new?tag=v${VERSION}"
        fi
    else
        echo -e "${YELLOW}Skipping git tag creation (--no-tag flag)${NC}"
    fi

    echo ""
    echo -e "${GREEN}🎉 Release complete!${NC}"
else
    echo -e "${RED}Error uploading to PyPI. Check the error above.${NC}"
    exit 1
fi
