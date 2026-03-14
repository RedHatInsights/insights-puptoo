#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function for logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate timestamp and define files to track
timestamp=$(date +%Y%m%d_%H%M%S)
PY_PKG_DEPS_FILES=(pyproject.toml poetry.lock requirements.txt requirements-dev.txt requirements-build.in requirements-build.txt)

log_info "Starting Python package dependencies bump-up process..."
echo "=========================================="

# Checkout to a new branch
branch_name="bump-up-py-pkg-deps-$timestamp"
log_info "Creating new branch: ${branch_name}"
if git checkout -b "$branch_name"; then
    log_success "Branch created successfully"
else
    log_error "Failed to create branch"
    exit 1
fi
echo ""

# Run make commands for python package dependencies bump up
log_info "Step 1/3: Generating poetry.lock and requirements files..."
if make generate-poetry-lock; then
    log_success "Poetry lock generation completed"
else
    log_error "Failed to generate poetry lock"
    exit 1
fi
echo ""

log_info "Step 2/3: Generating requirements-build.in..."
if make generate-requirements-build-in; then
    log_success "requirements-build.in generation completed"
else
    log_error "Failed to generate requirements-build.in"
    exit 1
fi
echo ""

log_info "Step 3/3: Generating requirements-build.txt..."
if make generate-requirements-build-txt; then
    log_success "requirements-build.txt generation completed"
else
    log_error "Failed to generate requirements-build.txt"
    exit 1
fi
echo ""

# Include the update of PY_PKG_DEPS_FILES to the commit, only if there are changes to the files
log_info "Checking for changes in package dependency files..."
if ! git diff --quiet ${PY_PKG_DEPS_FILES[@]}; then
    log_success "Changes detected in dependency files"

    log_info "Staging changes..."
    git add ${PY_PKG_DEPS_FILES[@]}

    log_info "Creating commit..."
    if git commit -m "Bump up python package dependencies" --signoff; then
        log_success "Commit created successfully"
    else
        log_error "Failed to create commit"
        exit 1
    fi

    log_info "Pushing branch to remote repository..."
    if git push origin "$branch_name"; then
        log_success "Branch pushed successfully"
    else
        log_error "Failed to push branch"
        exit 1
    fi

    echo ""
    echo "=========================================="
    log_success "Python package dependencies bump-up completed!"
    log_info "Branch: ${branch_name}"
    log_info "Next step: Create a pull request manually or run:"
    echo "  gh pr create --title \"Bump up python package dependencies\" --body \"Bump up python package dependencies\""

else
    log_warning "No changes detected in python package dependency files"
    log_info "Cleaning up branch..."
    git checkout -
    git branch -D "$branch_name"
    log_info "Process completed with no changes"
    exit 0
fi
