#!/bin/bash
#
# Cloudflare Worker Deployment Script (verse-sdk)
#
# This script deploys Cloudflare Workers for verse-based projects.
# It handles installation, authentication, deployment, and configuration.
#
# Usage:
#   verse-deploy [--status|--dry-run]
#   # Or from project root: path/to/deploy-cloudflare-worker.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Flags
MODE="deploy"
SHOW_HELP="false"
HAS_STATUS="false"
HAS_DRY_RUN="false"

for arg in "$@"; do
    case "$arg" in
        --status)
            MODE="status"
            HAS_STATUS="true"
            ;;
        --dry-run)
            MODE="dry-run"
            HAS_DRY_RUN="true"
            ;;
        -h|--help)
            SHOW_HELP="true"
            ;;
        *)
            ;;
    esac
done

if [ "$SHOW_HELP" = "true" ]; then
    echo "Usage: verse-deploy [--status|--dry-run]"
    echo ""
    echo "Modes:"
    echo "  (default) Deploy the Cloudflare Worker"
    echo "  --status  Show current worker status and exit"
    echo "  --dry-run Validate prerequisites and print planned actions"
    echo ""
    exit 0
fi

if [ "$HAS_STATUS" = "true" ] && [ "$HAS_DRY_RUN" = "true" ]; then
    error "Choose either --status or --dry-run (not both)"
fi

# Check if we're in the right directory
if [ ! -f "wrangler.toml" ] || [ ! -f "workers/cloudflare-worker.js" ]; then
    error "Please run this script from the project root directory (where wrangler.toml is located)"
fi

# Detect project name from wrangler.toml or directory name
PROJECT_NAME=""
if [ -f "wrangler.toml" ]; then
    PROJECT_NAME=$(grep -E "^name\s*=" wrangler.toml | head -1 | sed 's/.*=\s*"\?\([^"]*\)"\?.*/\1/' | tr '-' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
fi
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME=$(basename "$(pwd)" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
fi

echo ""
echo "=========================================="
echo "  Cloudflare Worker Deployment"
echo "  ${PROJECT_NAME}"
echo "=========================================="
echo ""

if [ "$MODE" = "status" ]; then
    info "Checking Node.js installation..."
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install it from https://nodejs.org/"
    fi
    success "Node.js is installed ($(node --version))"
    echo ""

    info "Checking Wrangler CLI..."
    if ! command -v wrangler &> /dev/null; then
        error "Wrangler CLI is required. Install it with: npm install -g wrangler"
    fi
    success "Wrangler CLI is installed ($(wrangler --version))"
    echo ""

    info "Checking Cloudflare authentication..."
    if ! wrangler whoami &> /dev/null; then
        error "Not authenticated with Cloudflare. Run: wrangler login"
    fi
    success "Authenticated with Cloudflare"
    echo ""

    info "Fetching deployment status..."
    echo ""
    WORKER_NAME=$(grep -E "^name\s*=" wrangler.toml | head -1 | sed 's/.*=\s*"\?\([^"]*\)"\?.*/\1/')
    if [ -z "$WORKER_NAME" ]; then
        error "Could not determine worker name from wrangler.toml"
    fi

    DEPLOY_JSON="$(mktemp)"
    if wrangler deployments list --name "$WORKER_NAME" --json &> "$DEPLOY_JSON"; then
        DEPLOY_JSON_PATH="$DEPLOY_JSON" python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["DEPLOY_JSON_PATH"])
data = json.loads(path.read_text()) if path.exists() else []
latest = data[0] if isinstance(data, list) and data else None

print("Worker:", latest.get("name") if latest else "unknown")
print("URL:", latest.get("url") if latest else "unknown")
print("Version ID:", latest.get("version_id") if latest else "unknown")
print("Deployed At:", latest.get("created_on") if latest else "unknown")

bindings = (latest.get("resources") or {}).get("bindings") if latest else None
if bindings:
    print("Bindings:")
    for b in bindings:
        name = b.get("name")
        btype = b.get("type")
        if name and btype:
            print(f"  - {name} ({btype})")
else:
    print("Bindings: none detected")
PY
        rm -f "$DEPLOY_JSON"
    else
        warning "Wrangler JSON output not available. Raw output:"
        wrangler deployments list --name "$WORKER_NAME"
    fi

    echo ""
    info "Secrets (names only):"
    wrangler secret list || warning "Failed to list secrets"
    echo ""

    success "Status check complete"
    exit 0
fi

if [ "$MODE" = "dry-run" ]; then
    info "Dry run: validating prerequisites and planned actions"
    echo ""

    if command -v node &> /dev/null; then
        success "Node.js is installed ($(node --version))"
    else
        warning "Node.js is not installed (required for deployment)"
    fi

    if command -v wrangler &> /dev/null; then
        success "Wrangler CLI is installed ($(wrangler --version))"
    else
        warning "Wrangler CLI is not installed (required for deployment)"
    fi

    if command -v wrangler &> /dev/null; then
        if wrangler whoami &> /dev/null; then
            success "Cloudflare authentication detected"
        else
            warning "Not authenticated with Cloudflare (run: wrangler login)"
        fi
    fi

    echo ""
    info "Planned actions:"
    echo "  • Deploy worker via: wrangler deploy"
    echo "  • Check/Set OPENAI_API_KEY secret"
    echo "  • Test worker endpoint"
    echo "  • Optionally update assets/js/guidance.js"
    echo ""
    success "Dry run complete (no changes made)"
    exit 0
fi

# Step 1: Check if Node.js is installed
info "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    error "Node.js is not installed. Please install it from https://nodejs.org/"
fi
success "Node.js is installed ($(node --version))"
echo ""

# Step 2: Check if wrangler is installed
info "Checking Wrangler CLI..."
if ! command -v wrangler &> /dev/null; then
    warning "Wrangler CLI is not installed."
    echo ""
    read -p "Would you like to install it now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Installing Wrangler CLI globally..."
        npm install -g wrangler || error "Failed to install Wrangler CLI"
        success "Wrangler CLI installed"
    else
        error "Wrangler CLI is required. Install it with: npm install -g wrangler"
    fi
else
    success "Wrangler CLI is installed ($(wrangler --version))"
fi
echo ""

# Step 3: Check if logged in to Cloudflare
info "Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    warning "Not logged in to Cloudflare."
    echo ""
    info "Opening browser for authentication..."
    wrangler login || error "Failed to authenticate with Cloudflare"
    success "Successfully authenticated"
else
    success "Already authenticated with Cloudflare"
fi
echo ""

# Step 4: Deploy the worker
info "Deploying worker to Cloudflare..."
echo ""
DEPLOY_OUTPUT=$(wrangler deploy 2>&1) || error "Failed to deploy worker"
echo "$DEPLOY_OUTPUT"
echo ""
success "Worker deployed successfully!"

# Extract worker URL from output
WORKER_URL=$(echo "$DEPLOY_OUTPUT" | grep -oE 'https://[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.workers\.dev' | head -1)

if [ -z "$WORKER_URL" ]; then
    warning "Could not extract worker URL from output. Please check the output above."
    read -p "Please enter your worker URL: " WORKER_URL
fi

echo ""
success "Worker URL: $WORKER_URL"
echo ""

# Step 5: Check if OPENAI_API_KEY secret is set
info "Checking if OPENAI_API_KEY secret is set..."
if wrangler secret list | grep -q "OPENAI_API_KEY"; then
    success "OPENAI_API_KEY secret is already set"
    echo ""
    read -p "Would you like to update it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Updating OPENAI_API_KEY secret..."
        wrangler secret put OPENAI_API_KEY || warning "Failed to update secret"
    fi
else
    warning "OPENAI_API_KEY secret is not set"
    echo ""
    read -p "Would you like to set it now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Setting OPENAI_API_KEY secret..."
        echo ""
        info "You can find your OpenAI API key at: https://platform.openai.com/api-keys"
        echo ""
        wrangler secret put OPENAI_API_KEY || error "Failed to set secret"
        success "OPENAI_API_KEY secret set"
    else
        warning "Worker will not work without OPENAI_API_KEY. Set it later with:"
        echo "  wrangler secret put OPENAI_API_KEY"
    fi
fi
echo ""

# Step 6: Test the worker
info "Testing worker..."
echo ""
TEST_RESPONSE=$(curl -s -X POST "$WORKER_URL" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 10
    }' 2>&1)

if echo "$TEST_RESPONSE" | grep -q "choices"; then
    success "Worker is working correctly!"
    echo ""
    info "Sample response:"
    echo "$TEST_RESPONSE" | head -n 3
else
    warning "Worker test failed. Response:"
    echo "$TEST_RESPONSE"
    echo ""
    warning "Please check:"
    echo "  1. Is OPENAI_API_KEY set correctly?"
    echo "  2. Does your OpenAI account have credits?"
    echo "  3. Check worker logs with: wrangler tail"
fi
echo ""

# Step 7: Update frontend configuration
info "Updating frontend configuration..."
echo ""

GUIDANCE_JS="assets/js/guidance.js"

if [ -f "$GUIDANCE_JS" ]; then
    # Check current WORKER_URL value
    CURRENT_URL=$(grep "const WORKER_URL = " "$GUIDANCE_JS" | sed "s/.*= '\(.*\)'.*/\1/")

    if [ -z "$CURRENT_URL" ]; then
        info "Current configuration: User-provided API key mode (WORKER_URL is empty)"
    else
        info "Current configuration: Worker mode ($CURRENT_URL)"
    fi

    echo ""
    read -p "Would you like to update WORKER_URL in $GUIDANCE_JS? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup original file
        cp "$GUIDANCE_JS" "${GUIDANCE_JS}.backup"

        # Update WORKER_URL
        sed -i.tmp "s|const WORKER_URL = '.*';|const WORKER_URL = '$WORKER_URL';|" "$GUIDANCE_JS"
        rm -f "${GUIDANCE_JS}.tmp"

        success "Updated WORKER_URL in $GUIDANCE_JS"
        info "Backup saved to ${GUIDANCE_JS}.backup"
        echo ""

        read -p "Would you like to commit and push this change? (y/n): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add "$GUIDANCE_JS"
            git commit -m "Enable Cloudflare Worker for spiritual guidance

Worker URL: $WORKER_URL

AI-Assisted-By: Codex"

            info "Pushing to GitHub..."
            git push || warning "Failed to push. Please push manually with: git push"

            success "Changes committed and pushed!"
            echo ""
            info "GitHub Pages will rebuild in 1-2 minutes."
            info "Then visit: https://sanatan-learnings.github.io/hanuman-chalisa/guidance"
        else
            warning "Changes not committed. Commit manually when ready:"
            echo "  git add $GUIDANCE_JS"
            echo "  git commit -m \"Enable Cloudflare Worker\""
            echo "  git push"
        fi
    else
        info "Skipped updating $GUIDANCE_JS"
        echo ""
        info "To enable the worker, update this line in $GUIDANCE_JS:"
        echo "  const WORKER_URL = '$WORKER_URL';"
    fi
else
    warning "Could not find $GUIDANCE_JS"
    info "Manually update WORKER_URL in your guidance.js file to:"
    echo "  const WORKER_URL = '$WORKER_URL';"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
success "Worker deployed and configured"
echo ""
info "Summary:"
echo "  • Worker URL: $WORKER_URL"
echo "  • View metrics: https://dash.cloudflare.com/"
echo "  • View logs: wrangler tail"
echo "  • Redeploy: ./scripts/deploy-cloudflare-worker.sh"
echo ""

if [ -z "$CURRENT_URL" ] || [ "$CURRENT_URL" != "$WORKER_URL" ]; then
    info "Next steps:"
    echo "  1. Wait 1-2 minutes for GitHub Pages to rebuild"
    echo "  2. Visit: https://sanatan-learnings.github.io/hanuman-chalisa/guidance"
    echo "  3. Try asking a spiritual question (no API key needed!)"
    echo ""
fi

info "To disable the worker, set WORKER_URL = '' in $GUIDANCE_JS and push"
echo ""
