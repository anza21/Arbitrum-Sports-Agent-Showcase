#!/bin/bash

# --- START OF ATOMIC SCRIPT ---
# Superior Agents - Public Repository Synchronization Script
# This script safely syncs the private project to the public showcase repository

# Step 1: Define paths for clarity
PRIVATE_PROJECT_ROOT="/home/anza/project/superior-agents-clean/superior-agent-v1"
PUBLIC_REPO_URL="git@github.com:anza21/Arbitrum-Sports-Agent-Showcase.git"
TEMP_PUBLIC_DIR="/home/anza/Desktop/public_repo_temp_clone"

# Step 2: Prepare a clean workspace by cloning the public repo into a temporary directory
echo "INFO: Preparing a clean workspace..."
rm -rf "$TEMP_PUBLIC_DIR"
git clone "$PUBLIC_REPO_URL" "$TEMP_PUBLIC_DIR"

# Step 3: Use rsync to securely sync the updated code, excluding all sensitive files
echo "INFO: Syncing updated source code securely..."
rsync -av --delete \
--exclude '.git/' \
--exclude '.idea/' \
--exclude 'agent/db/*.db' \
--exclude 'db/*.db' \
--exclude 'Report_*.txt' \
--exclude '*.pyc' \
--exclude '__pycache__/' \
--exclude '*.log' \
--exclude 'agent/.env' \
--exclude '.env' \
--exclude '*.key' \
--exclude '*.pem' \
--exclude 'node_modules/' \
--exclude 'venv/' \
--exclude 'agent-venv/' \
--exclude '.venv/' \
"$PRIVATE_PROJECT_ROOT/" "$TEMP_PUBLIC_DIR/"

# Step 4: Re-create the safe .env.example file to reflect any new required variables
echo "INFO: Re-creating the safe .env.example file..."
if [ -f "$PRIVATE_PROJECT_ROOT/agent/.env" ]; then
    grep -v '^#' "$PRIVATE_PROJECT_ROOT/agent/.env" | sed 's/=.*/=/' > "$TEMP_PUBLIC_DIR/agent/.env.example"
else
    echo "# Environment variables template" > "$TEMP_PUBLIC_DIR/agent/.env.example"
    echo "# Copy this file to .env and fill in your actual values" >> "$TEMP_PUBLIC_DIR/agent/.env.example"
fi

# Step 5: Navigate into the public repo's directory, commit, and push the changes
echo "INFO: Committing and pushing updates to the public GitHub repo..."
cd "$TEMP_PUBLIC_DIR"
git add .

# Check if there are changes to commit to avoid an error
if ! git diff-index --quiet HEAD; then
    git commit -m "sync: Update project with latest stable version from private repository

- Synchronized latest code changes
- Updated documentation and configuration
- Maintained security by excluding sensitive files
- Generated fresh .env.example template"
    git push origin main
    echo "INFO: Changes committed and pushed successfully"
else
    echo "INFO: No changes detected, repository is already up to date"
fi

# Step 6: Clean up the temporary directory
echo "INFO: Cleaning up workspace..."
rm -rf "$TEMP_PUBLIC_DIR"

echo "INFO: ATOMIC SCRIPT COMPLETED. Public showcase repository is now up to date."
# --- END OF ATOMIC SCRIPT ---
