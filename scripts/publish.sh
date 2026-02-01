#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}  PyPI Publishing Script${NC}"
echo -e "${BLUE}  verse-content-sdk${NC}"
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

# Ask if user wants to update version
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

echo ""
echo -e "${YELLOW}Publishing version: ${GREEN}${VERSION}${NC}"
echo ""

# Clean old builds
echo -e "${YELLOW}Cleaning old builds...${NC}"
rm -rf dist/ build/ verse_content_sdk.egg-info/
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

# Ask to upload to TestPyPI first
read -p "Upload to TestPyPI first for testing? (recommended, y/n): " TEST_UPLOAD

if [ "$TEST_UPLOAD" = "y" ] || [ "$TEST_UPLOAD" = "Y" ]; then
    echo ""
    echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
    python -m twine upload --repository testpypi dist/*

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully uploaded to TestPyPI${NC}"
        echo ""
        echo -e "${BLUE}View your package at:${NC}"
        echo -e "https://test.pypi.org/project/verse-content-sdk/${VERSION}/"
        echo ""
        echo -e "${YELLOW}Test installation with:${NC}"
        echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ verse-content-sdk"
        echo ""
    else
        echo -e "${RED}Error uploading to TestPyPI. Check the error above.${NC}"
        exit 1
    fi
fi

# Confirm before uploading to production PyPI
echo ""
echo -e "${RED}⚠️  WARNING: You are about to upload to PRODUCTION PyPI${NC}"
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (y/yes): " CONFIRM

if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Upload cancelled.${NC}"
    exit 0
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
    echo -e "https://pypi.org/project/verse-content-sdk/${VERSION}/"
    echo ""
    echo -e "${BLUE}Install with:${NC}"
    echo "pip install verse-content-sdk"
    echo ""

    # Ask about git tagging
    read -p "Create git tag and push? (y/n): " CREATE_TAG

    if [ "$CREATE_TAG" = "y" ] || [ "$CREATE_TAG" = "Y" ]; then
        git add setup.py
        git commit -m "Bump version to ${VERSION}" || true
        git tag -a "v${VERSION}" -m "Release version ${VERSION}"
        git push origin main
        git push origin "v${VERSION}"

        echo -e "${GREEN}✓ Git tag created and pushed${NC}"
        echo ""
        echo -e "${BLUE}Create GitHub release at:${NC}"
        echo "https://github.com/sanatan-learnings/verse-content-sdk/releases/new?tag=v${VERSION}"
    fi

    echo ""
    echo -e "${GREEN}🎉 Release complete!${NC}"
else
    echo -e "${RED}Error uploading to PyPI. Check the error above.${NC}"
    exit 1
fi
