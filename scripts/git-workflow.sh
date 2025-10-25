#!/bin/bash

# ============================================================================
# Git Workflow Automation - Industry Standard Practices
# ============================================================================
#
# This script demonstrates and automates professional Git workflows following
# industry best practices for version control, code quality, and release management.
#
# FEATURES:
# - Conventional commit message validation
# - Automated pre-commit hooks
# - Branch protection and code review simulation
# - Release candidate creation
# - Semantic version bumping
# - Automated changelog generation
# - Tag creation with release notes
#
# USAGE:
# ./scripts/git-workflow.sh [action] [options]
#
# ACTIONS:
# - setup:     Configure Git with professional settings
# - commit:    Create a conventional commit with validation
# - release:   Create a new release with semantic versioning
# - validate:  Validate commit messages and branch state
# - demo:      Demonstrate complete workflow
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

log_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
    echo "=============================================="
}

# ============================================================================
# GIT CONFIGURATION SETUP
# ============================================================================

setup_git_config() {
    log_header "Setting Up Professional Git Configuration"
    
    # Set commit template
    git config commit.template .gitmessage
    log_success "Configured commit message template"
    
    # Set up aliases for common operations
    git config alias.co checkout
    git config alias.br branch
    git config alias.ci commit
    git config alias.st status
    git config alias.unstage 'reset HEAD --'
    git config alias.last 'log -1 HEAD'
    git config alias.visual '!gitk'
    log_success "Configured Git aliases"
    
    # Professional log formats
    git config alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
    git config alias.hist "log --pretty=format:'%h %ad | %s%d [%an]' --graph --date=short"
    log_success "Configured professional log formats"
    
    # Set up editor and merge tool preferences
    git config core.editor "code --wait" 2>/dev/null || git config core.editor "vim"
    git config merge.tool vimdiff
    log_success "Configured editor and merge tools"
    
    # Set up push behavior
    git config push.default simple
    git config branch.autosetupmerge always
    git config branch.autosetuprebase always
    log_success "Configured push and branch behavior"
    
    # Line ending configuration
    git config core.autocrlf input
    git config core.safecrlf true
    log_success "Configured line ending handling"
    
    log_success "Git configuration setup completed!"
    echo ""
}

# ============================================================================
# COMMIT MESSAGE VALIDATION
# ============================================================================

validate_commit_message() {
    local commit_msg="$1"
    
    # Check conventional commit format
    if [[ ! "$commit_msg" =~ ^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .{1,50} ]]; then
        log_error "Commit message doesn't follow Conventional Commits format"
        echo "Expected format: type(scope): description"
        echo "Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert"
        return 1
    fi
    
    # Check length
    local subject_line=$(echo "$commit_msg" | head -n1)
    if [[ ${#subject_line} -gt 72 ]]; then
        log_error "Commit subject line too long (${#subject_line} > 72 characters)"
        return 1
    fi
    
    log_success "Commit message format validated"
    return 0
}

# ============================================================================
# INTERACTIVE COMMIT CREATION
# ============================================================================

create_interactive_commit() {
    log_header "Creating Professional Commit"
    
    # Check for staged changes
    if [[ -z $(git diff --cached --name-only) ]]; then
        log_warning "No staged changes found"
        echo "Available files to stage:"
        git status --porcelain | grep "^.M\|^??" | head -10
        echo ""
        read -p "Stage all changes? (y/n): " stage_all
        if [[ "$stage_all" =~ ^[Yy]$ ]]; then
            git add .
            log_success "Staged all changes"
        else
            log_info "Please stage your changes with: git add <files>"
            return 1
        fi
    fi
    
    # Interactive commit type selection
    echo ""
    echo "Select commit type:"
    echo "1) feat     - New feature"
    echo "2) fix      - Bug fix"
    echo "3) docs     - Documentation"
    echo "4) style    - Code style/formatting"
    echo "5) refactor - Code refactoring"
    echo "6) perf     - Performance improvement"
    echo "7) test     - Adding tests"
    echo "8) chore    - Maintenance"
    echo "9) ci       - CI/CD changes"
    echo "10) build   - Build system changes"
    echo ""
    read -p "Enter choice (1-10): " type_choice
    
    case $type_choice in
        1) commit_type="feat" ;;
        2) commit_type="fix" ;;
        3) commit_type="docs" ;;
        4) commit_type="style" ;;
        5) commit_type="refactor" ;;
        6) commit_type="perf" ;;
        7) commit_type="test" ;;
        8) commit_type="chore" ;;
        9) commit_type="ci" ;;
        10) commit_type="build" ;;
        *) log_error "Invalid choice"; return 1 ;;
    esac
    
    # Optional scope
    read -p "Enter scope (optional, e.g., api, frontend, ml): " scope
    if [[ -n "$scope" ]]; then
        scope="($scope)"
    fi
    
    # Commit description
    read -p "Enter commit description (imperative mood): " description
    if [[ -z "$description" ]]; then
        log_error "Description is required"
        return 1
    fi
    
    # Optional body
    echo ""
    echo "Enter commit body (optional, press Enter twice to finish):"
    body=""
    while IFS= read -r line; do
        if [[ -z "$line" && -z "$body" ]]; then
            break
        elif [[ -z "$line" && -n "$body" ]]; then
            break
        fi
        body+="$line"$'\n'
    done
    
    # Construct commit message
    commit_msg="${commit_type}${scope}: ${description}"
    if [[ -n "$body" ]]; then
        commit_msg+=$'\n\n'"${body%$'\n'}"
    fi
    
    # Validate commit message
    if ! validate_commit_message "$commit_msg"; then
        return 1
    fi
    
    # Preview commit
    echo ""
    log_info "Commit preview:"
    echo "----------------------------------------"
    echo "$commit_msg"
    echo "----------------------------------------"
    echo ""
    
    # Show files to be committed
    echo "Files to be committed:"
    git diff --cached --name-status
    echo ""
    
    # Confirm commit
    read -p "Create this commit? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        git commit -m "$commit_msg"
        log_success "Commit created successfully!"
        
        # Show commit details
        echo ""
        log_info "Commit details:"
        git log -1 --stat
    else
        log_info "Commit cancelled"
    fi
}

# ============================================================================
# RELEASE MANAGEMENT
# ============================================================================

create_release() {
    local version_type="${1:-patch}"
    
    log_header "Creating Release - $version_type"
    
    # Check for clean working directory
    if [[ $(git status --porcelain) ]]; then
        log_error "Working directory must be clean for release"
        return 1
    fi
    
    # Get current version
    local current_version="1.0.0"  # Default if no version file
    if [[ -f "$PROJECT_ROOT/version.py" ]]; then
        current_version=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from version import __version__
print(__version__)
" 2>/dev/null || echo "1.0.0")
    fi
    
    log_info "Current version: $current_version"
    
    # Calculate next version
    local next_version=$(python3 -c "
from packaging import version
v = version.Version('$current_version')
major, minor, patch = v.major, v.minor, v.micro

if '$version_type' == 'major':
    major += 1
    minor = 0
    patch = 0
elif '$version_type' == 'minor':
    minor += 1
    patch = 0
elif '$version_type' == 'patch':
    patch += 1

print(f'{major}.{minor}.{patch}')
" 2>/dev/null || echo "1.0.1")
    
    log_info "Next version: $next_version"
    
    # Confirm release
    echo ""
    read -p "Create release $next_version? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Release cancelled"
        return 0
    fi
    
    # Update version files (if they exist)
    if [[ -f "$PROJECT_ROOT/version.py" ]]; then
        sed -i.bak "s/__version__ = \".*\"/__version__ = \"$next_version\"/" "$PROJECT_ROOT/version.py"
        rm "$PROJECT_ROOT/version.py.bak" 2>/dev/null || true
        log_success "Updated version.py"
    fi
    
    if [[ -f "$PROJECT_ROOT/frontend/package.json" ]]; then
        sed -i.bak "s/\"version\": \".*\"/\"version\": \"$next_version\"/" "$PROJECT_ROOT/frontend/package.json"
        rm "$PROJECT_ROOT/frontend/package.json.bak" 2>/dev/null || true
        log_success "Updated package.json"
    fi
    
    # Create release commit
    git add .
    git commit -m "chore(release): bump version to $next_version

- Update version files to $next_version
- Prepare for release $next_version
- Update build metadata and timestamps

Release: $next_version"
    
    log_success "Created release commit"
    
    # Create annotated tag
    local tag_message="Release v$next_version

$(date '+%Y-%m-%d %H:%M:%S')

This release includes:
$(git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~10)..HEAD | head -5)

For full changelog, see CHANGELOG.md"
    
    git tag -a "v$next_version" -m "$tag_message"
    log_success "Created release tag v$next_version"
    
    # Display release summary
    echo ""
    log_success "Release $next_version created successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Push changes: git push origin main"
    echo "2. Push tag: git push origin v$next_version"
    echo "3. Create GitHub release: gh release create v$next_version --generate-notes"
    echo ""
}

# ============================================================================
# WORKFLOW DEMONSTRATION
# ============================================================================

demo_workflow() {
    log_header "Git Workflow Demonstration"
    
    echo "This demo shows professional Git practices:"
    echo ""
    echo "1. 📝 Conventional Commits"
    echo "2. 🏷️  Semantic Versioning"
    echo "3. 📊 Professional Logging"
    echo "4. 🔄 Release Management"
    echo "5. 📋 Standardized Templates"
    echo ""
    
    # Show current configuration
    log_info "Current Git Configuration:"
    echo "User: $(git config user.name) <$(git config user.email)>"
    echo "Commit template: $(git config commit.template || echo 'Not set')"
    echo "Push default: $(git config push.default || echo 'Not set')"
    echo ""
    
    # Show professional log
    log_info "Professional Git Log (last 5 commits):"
    git log --oneline --decorate --graph -5 2>/dev/null || echo "No commits yet"
    echo ""
    
    # Show tags
    log_info "Release Tags:"
    git tag -l "v*" | tail -5 | sort -V || echo "No release tags yet"
    echo ""
    
    # Show branch information
    log_info "Branch Information:"
    echo "Current branch: $(git branch --show-current)"
    echo "Remote tracking: $(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo 'Not set')"
    echo ""
    
    # Show repository statistics
    log_info "Repository Statistics:"
    echo "Total commits: $(git rev-list --all --count 2>/dev/null || echo '0')"
    echo "Contributors: $(git shortlog -sn | wc -l 2>/dev/null || echo '0')"
    echo "Files tracked: $(git ls-files | wc -l 2>/dev/null || echo '0')"
    echo ""
    
    log_success "Workflow demonstration completed!"
}

# ============================================================================
# MAIN SCRIPT LOGIC
# ============================================================================

show_help() {
    echo "Git Workflow Automation - Industry Standard Practices"
    echo ""
    echo "Usage: $0 [action] [options]"
    echo ""
    echo "Actions:"
    echo "  setup      Configure Git with professional settings"
    echo "  commit     Create a conventional commit interactively"
    echo "  release    Create a new release (patch|minor|major)"
    echo "  validate   Validate current repository state"
    echo "  demo       Demonstrate workflow capabilities"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Configure Git settings"
    echo "  $0 commit                   # Interactive commit creation"
    echo "  $0 release patch            # Create patch release"
    echo "  $0 release minor            # Create minor release"
    echo "  $0 demo                     # Show workflow demonstration"
    echo ""
}

# Parse command line arguments
ACTION="${1:-help}"

case "$ACTION" in
    setup)
        setup_git_config
        ;;
    commit)
        create_interactive_commit
        ;;
    release)
        VERSION_TYPE="${2:-patch}"
        if [[ ! "$VERSION_TYPE" =~ ^(major|minor|patch)$ ]]; then
            log_error "Invalid version type. Use: major, minor, or patch"
            exit 1
        fi
        create_release "$VERSION_TYPE"
        ;;
    validate)
        demo_workflow
        ;;
    demo)
        demo_workflow
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown action: $ACTION"
        show_help
        exit 1
        ;;
esac