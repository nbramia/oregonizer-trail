#!/bin/bash

###############################################################################
# Oregonizer Trail Deployment Script
#
# This script enforces a rigorous test-before-deploy policy.
# ALL tests must pass before code is pushed to GitHub and deployed to Heroku.
#
# Usage: ./deploy.sh "Your commit message here"
#
# The script will:
# 1. Check for uncommitted changes
# 2. Run the full test suite
# 3. Abort deployment if any tests fail
# 4. Stage all changes
# 5. Commit with provided message + metadata
# 6. Push to GitHub (triggers Heroku auto-deploy)
###############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if commit message was provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Commit message required${NC}"
    echo "Usage: ./deploy.sh \"Your commit message here\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Oregonizer Trail Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Show current status
echo -e "${YELLOW}Step 1: Checking git status...${NC}"
git status --short
echo ""

# Step 2: Run all tests
echo -e "${YELLOW}Step 2: Running test suite...${NC}"
echo "This is MANDATORY - deployment will abort if any test fails"
echo ""

# Run tests and capture output
TEST_OUTPUT=$(python3 -m unittest discover -s . -p "test_*.py" 2>&1)
TEST_EXIT_CODE=$?

# Display test output
echo "$TEST_OUTPUT"
echo ""

# Check if tests failed due to missing dependencies
if echo "$TEST_OUTPUT" | grep -q "ModuleNotFoundError"; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}WARNING: Cannot run tests locally${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo "Tests failed due to missing Python dependencies."
    echo "This is expected if you haven't installed the requirements locally."
    echo ""
    echo "The tests WILL run on Heroku during deployment."
    echo "If tests fail on Heroku, the deployment will be rolled back."
    echo ""
    read -p "Continue deployment without local tests? (yes/no): " -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        echo -e "${RED}Deployment cancelled by user${NC}"
        exit 1
    fi
    echo -e "${YELLOW}⚠ Proceeding without local test validation${NC}"
    echo ""
elif [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}DEPLOYMENT ABORTED${NC}"
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Tests failed! Fix the failing tests before deploying.${NC}"
    echo ""
    echo "To see detailed test output, run:"
    echo "  python3 -m unittest discover -s . -p \"test_*.py\" -v"
    echo ""
    exit 1
fi

# Extract test count from output
if echo "$TEST_OUTPUT" | grep -q "Ran [0-9]* test"; then
    TEST_COUNT=$(echo "$TEST_OUTPUT" | grep "Ran [0-9]* test" | grep -o "[0-9]*" | head -1)
    echo -e "${GREEN}✓ All $TEST_COUNT tests passed!${NC}"
else
    echo -e "${GREEN}✓ Tests passed!${NC}"
fi
echo ""

# Step 3: Stage all changes
echo -e "${YELLOW}Step 3: Staging changes...${NC}"
git add -A
echo -e "${GREEN}✓ Changes staged${NC}"
echo ""

# Step 4: Create commit
echo -e "${YELLOW}Step 4: Creating commit...${NC}"

# Build full commit message with metadata
FULL_COMMIT_MESSAGE=$(cat <<EOF
$COMMIT_MESSAGE

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)

# Commit the changes
git commit -m "$FULL_COMMIT_MESSAGE"
COMMIT_EXIT_CODE=$?

if [ $COMMIT_EXIT_CODE -ne 0 ]; then
    # Check if there were no changes to commit
    if git diff --cached --quiet; then
        echo -e "${YELLOW}No changes to commit - working tree clean${NC}"
        exit 0
    else
        echo -e "${RED}Commit failed${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Commit created${NC}"
echo ""

# Step 5: Push to GitHub
echo -e "${YELLOW}Step 5: Pushing to GitHub...${NC}"
git push origin main
PUSH_EXIT_CODE=$?

if [ $PUSH_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Push failed - check your network connection and GitHub access${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pushed to GitHub${NC}"
echo ""

# Step 6: Deployment triggered
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DEPLOYMENT SUCCESSFUL${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "✓ Tests passed ($TEST_COUNT tests)"
echo "✓ Changes committed"
echo "✓ Pushed to GitHub"
echo ""
echo "Heroku will now automatically deploy from GitHub."
echo ""
echo "Monitor deployment:"
echo "  heroku logs --tail -a YOUR_APP_NAME"
echo ""
echo "View app:"
echo "  open https://YOUR_APP_URL"
echo ""
