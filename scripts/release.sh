#!/bin/bash

# ============================================================================
# Release Management Script - Industry Standard Versioning
# ============================================================================
#
# This script automates version management, tagging, and release preparation
# following Semantic Versioning (SemVer) and industry best practices.
#
# FEATURES:
# - Semantic version bumping (major, minor, patch)
# - Automated changelog generation from conventional commits
# - Git tagging with release notes
# - Build metadata injection
# - Release artifact preparation
# - GitHub release creation (optional)
#
# USAGE:
# ./scripts/release.sh [major|minor|patch] [--dry-run] [--push]
#
# EXAMPLES:
# ./scripts/release.sh patch              # Bump patch version (1.0.0 -> 1.0.1)
# ./scripts/release.sh minor              # Bump minor version (1.0.1 -> 1.1.0)
# ./scripts/release.sh major              # Bump major version (1.1.0 -> 2.0.0)
# ./scripts/release.sh patch --dry-run    # Preview changes without applying
# ./scripts/release.sh minor --push       # Create release and push to origin
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_ROOT/version.py"
CHANGELOG_FILE="$PROJECT_ROOT/CHANGELOG.md"
PACKAGE_JSON="$PROJECT_ROOT/frontend/package.json"

# Parse command line arguments
BUMP_TYPE="${1:-patch}"
DRY_RUN=false
PUSH_CHANGES=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --push)
            PUSH_CHANGES=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [major|minor|patch] [--dry-run] [--push]"
            echo ""
            echo "Options:"
            echo "  major         Bump major version (breaking changes)"
            echo "  minor         Bump minor version (new features)"
            echo "  patch         Bump patch version (bug fixes)"
            echo "  --dry-run     Preview changes without applying them"
            echo "  --push        Push changes and tags to remote repository"
            echo "  --help        Show this help message"
            exit 0
            ;;
    esac
done

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED}❌ Error: Invalid bump type '$BUMP_TYPE'. Use: major, minor, or patch${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Aquaculture ML Platform - Release Management${NC}"
echo "=============================================="

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository!"
        exit 1
    fi
}

# Check for uncommitted changes
check_working_directory() {
    if [[ $(git status --porcelain) ]]; then
        log_error "Working directory has uncommitted changes!"
        echo "Please commit or stash your changes before creating a release."
        exit 1
    fi
}

# Get current version from version.py
get_current_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from version import __version__
print(__version__)
"
    else
        echo "0.0.0"
    fi
}

# Calculate next version based on bump type
calculate_next_version() {
    local current_version="$1"
    local bump_type="$2"
    
    python3 -c "
import sys
from packaging import version

try:
    v = version.Version('$current_version')
    major, minor, patch = v.major, v.minor, v.micro
    
    if '$bump_type' == 'major':
        major += 1
        minor = 0
        patch = 0
    elif '$bump_type' == 'minor':
        minor += 1
        patch = 0
    elif '$bump_type' == 'patch':
        patch += 1
    
    print(f'{major}.{minor}.{patch}')
except Exception as e:
    print('Error: Invalid version format', file=sys.stderr)
    sys.exit(1)
"
}

# Update version in version.py
update_version_file() {
    local new_version="$1"
    local release_date="$(date +%Y-%m-%d)"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would update $VERSION_FILE with version $new_version"
        return
    fi
    
    # Get current git commit information
    local commit_hash="$(git rev-parse HEAD)"
    local commit_date="$(git log -1 --format=%ci)"
    local branch="$(git rev-parse --abbrev-ref HEAD)"
    local build_date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    # Update version.py with new version and build info
    python3 -c "
import re
import sys

version_file = '$VERSION_FILE'
new_version = '$new_version'
parts = new_version.split('.')

# Read current file
with open(version_file, 'r') as f:
    content = f.read()

# Update version string
content = re.sub(r'__version__ = \"[^\"]*\"', f'__version__ = \"{new_version}\"', content)

# Update version_info
version_info_pattern = r'__version_info__ = \{[^}]*\}'
version_info_replacement = f'''__version_info__ = {{
    \"major\": {parts[0]},
    \"minor\": {parts[1]},
    \"patch\": {parts[2]},
    \"prerelease\": None,
    \"build\": None
}}'''
content = re.sub(version_info_pattern, version_info_replacement, content, flags=re.DOTALL)

# Update release date
content = re.sub(r'RELEASE_DATE = \"[^\"]*\"', f'RELEASE_DATE = \"$release_date\"', content)

# Update build info
build_info_pattern = r'BUILD_INFO = \{[^}]*\}'
build_info_replacement = f'''BUILD_INFO = {{
    \"build_number\": None,
    \"commit_hash\": \"$commit_hash\",
    \"commit_date\": \"$commit_date\",
    \"branch\": \"$branch\",
    \"build_date\": \"$build_date\",
    \"ci_system\": None,
    \"docker_image\": None
}}'''
content = re.sub(build_info_pattern, build_info_replacement, content, flags=re.DOTALL)

# Write updated content
with open(version_file, 'w') as f:
    f.write(content)

print(f'Updated {version_file} to version {new_version}')
"
}

# Update frontend package.json version
update_package_json() {
    local new_version="$1"
    
    if [[ -f "$PACKAGE_JSON" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would update $PACKAGE_JSON with version $new_version"
            return
        fi
        
        # Update package.json version
        python3 -c "
import json

with open('$PACKAGE_JSON', 'r') as f:
    data = json.load(f)

data['version'] = '$new_version'

with open('$PACKAGE_JSON', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')

print(f'Updated package.json to version $new_version')
"
    fi
}

# Generate changelog entry
generate_changelog_entry() {
    local version="$1"
    local date="$(date +%Y-%m-%d)"
    
    # Get commits since last tag
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    local commit_range
    
    if [[ -n "$last_tag" ]]; then
        commit_range="${last_tag}..HEAD"
    else
        commit_range="HEAD"
    fi
    
    # Generate changelog from conventional commits
    python3 -c "
import subprocess
import re
from collections import defaultdict

def get_commits(commit_range):
    try:
        result = subprocess.run(['git', 'log', '$commit_range', '--oneline', '--no-merges'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def parse_commit(commit_line):
    # Parse conventional commit format
    match = re.match(r'[a-f0-9]+ (\w+)(?:\(([^)]+)\))?: (.+)', commit_line)
    if match:
        commit_type, scope, description = match.groups()
        return {
            'type': commit_type,
            'scope': scope or '',
            'description': description,
            'raw': commit_line
        }
    return {'type': 'other', 'scope': '', 'description': commit_line, 'raw': commit_line}

def categorize_commits(commits):
    categories = defaultdict(list)
    type_mapping = {
        'feat': 'Features',
        'fix': 'Bug Fixes',
        'docs': 'Documentation', 
        'style': 'Code Style',
        'refactor': 'Code Refactoring',
        'perf': 'Performance Improvements',
        'test': 'Tests',
        'chore': 'Maintenance',
        'ci': 'CI/CD',
        'build': 'Build System',
        'revert': 'Reverts'
    }
    
    for commit in commits:
        parsed = parse_commit(commit)
        category = type_mapping.get(parsed['type'], 'Other Changes')
        categories[category].append(parsed)
    
    return categories

# Generate changelog entry
commits = get_commits('$commit_range')
if commits and commits[0]:  # Check if we have actual commits
    categories = categorize_commits(commits)
    
    changelog_entry = f'''
## [{version}] - {date}

'''
    
    # Add categories in order of importance
    category_order = [
        'Features', 'Bug Fixes', 'Performance Improvements',
        'Documentation', 'Code Refactoring', 'Tests',
        'CI/CD', 'Build System', 'Maintenance', 'Other Changes'
    ]
    
    for category in category_order:
        if category in categories:
            changelog_entry += f'### {category}\n\n'
            for commit in categories[category]:
                scope_str = f'**{commit[\"scope\"]}**: ' if commit['scope'] else ''
                changelog_entry += f'- {scope_str}{commit[\"description\"]}\n'
            changelog_entry += '\n'
    
    print(changelog_entry.strip())
else:
    print(f'''
## [{version}] - {date}

### Changes
- Version bump to {version}
'''.strip())
"
}

# Update changelog file
update_changelog() {
    local version="$1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would update CHANGELOG.md with new entry for version $version"
        return
    fi
    
    local changelog_entry=$(generate_changelog_entry "$version")
    
    if [[ -f "$CHANGELOG_FILE" ]]; then
        # Insert new entry after header
        python3 -c "
import re

changelog_file = '$CHANGELOG_FILE'
new_entry = '''$changelog_entry'''

with open(changelog_file, 'r') as f:
    content = f.read()

# Find the first ## heading (excluding the main title)
lines = content.split('\n')
header_end = 0
for i, line in enumerate(lines):
    if line.startswith('## [') and i > 0:
        header_end = i
        break

if header_end > 0:
    # Insert new entry before first release entry
    lines.insert(header_end, new_entry)
    lines.insert(header_end, '')  # Add blank line
else:
    # No existing entries, add after header
    for i, line in enumerate(lines):
        if line.strip() == '' and i > 0:
            lines.insert(i + 1, new_entry)
            break

with open(changelog_file, 'w') as f:
    f.write('\n'.join(lines))

print(f'Updated {changelog_file}')
"
    else
        # Create new changelog file
        cat > "$CHANGELOG_FILE" << EOF
# Changelog

All notable changes to the Aquaculture ML Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

$changelog_entry
EOF
    fi
}

# Create git tag with release notes
create_git_tag() {
    local version="$1"
    local tag_name="v$version"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would create git tag $tag_name"
        return
    fi
    
    # Create annotated tag with release notes
    local release_notes="Release $version

$(generate_changelog_entry "$version" | sed '/^## \[/d' | sed '/^$/d')"
    
    git tag -a "$tag_name" -m "$release_notes"
    log_success "Created git tag $tag_name"
}

# ============================================================================
# MAIN RELEASE PROCESS
# ============================================================================

log_info "Starting release process for $BUMP_TYPE version bump"

# Pre-flight checks
log_info "Running pre-flight checks..."
check_git_repo

if [[ "$DRY_RUN" != "true" ]]; then
    check_working_directory
fi

# Get current and next version
current_version=$(get_current_version)
next_version=$(calculate_next_version "$current_version" "$BUMP_TYPE")

if [[ -z "$next_version" || "$next_version" == "Error"* ]]; then
    log_error "Failed to calculate next version"
    exit 1
fi

log_info "Current version: $current_version"
log_info "Next version: $next_version"

if [[ "$DRY_RUN" == "true" ]]; then
    log_warning "DRY RUN MODE - No changes will be applied"
fi

# Update version files
log_info "Updating version files..."
update_version_file "$next_version"
update_package_json "$next_version"

# Update changelog
log_info "Updating changelog..."
update_changelog "$next_version"

if [[ "$DRY_RUN" != "true" ]]; then
    # Stage changes
    git add "$VERSION_FILE" "$CHANGELOG_FILE"
    
    if [[ -f "$PACKAGE_JSON" ]]; then
        git add "$PACKAGE_JSON"
    fi
    
    # Create release commit
    git commit -m "chore(release): bump version to $next_version

- Update version.py to $next_version
- Update package.json version
- Update CHANGELOG.md with release notes
- Add build metadata and commit information

Release: $next_version"
    
    log_success "Created release commit"
    
    # Create git tag
    create_git_tag "$next_version"
    
    # Push changes if requested
    if [[ "$PUSH_CHANGES" == "true" ]]; then
        log_info "Pushing changes to remote repository..."
        git push origin main
        git push origin "v$next_version"
        log_success "Pushed changes and tags to remote repository"
    fi
fi

# Display release summary
echo ""
echo -e "${GREEN}🎉 Release $next_version preparation complete!${NC}"
echo "=============================================="
echo "Version: $current_version → $next_version"
echo "Type: $BUMP_TYPE"
echo "Tag: v$next_version"

if [[ "$DRY_RUN" != "true" ]]; then
    echo ""
    echo "Next steps:"
    if [[ "$PUSH_CHANGES" != "true" ]]; then
        echo "1. Review the changes: git log --oneline -2"
        echo "2. Push to remote: git push origin main && git push origin v$next_version"
    fi
    echo "3. Create GitHub release: gh release create v$next_version --generate-notes"
    echo "4. Deploy to production: ./scripts/deploy.sh production v$next_version"
    echo "5. Update Docker images: docker build -t aquaculture:$next_version ."
fi

log_success "Release process completed successfully!"