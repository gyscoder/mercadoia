#!/bin/bash

# Simple Git automation script for the Bot de Investimentos project
# Usage: ./git-auto.sh "Commit message"

# Check if commit message provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"Commit message\""
    echo "Example: $0 \"Add data collection script\""
    exit 1
fi

# Git commands
git add .
git commit -m "$1"
git push origin main

echo "Changes committed and pushed successfully!"