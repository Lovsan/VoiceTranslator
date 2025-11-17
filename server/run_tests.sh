#!/bin/bash

# run_tests.sh - Quick test script for VoiceTranslator server

echo "========================================"
echo "  VoiceTranslator Server Test Runner"
echo "========================================"
echo ""

# Change to server directory
cd "$(dirname "$0")"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements-dev.txt
fi

echo "🧪 Running tests..."
echo ""

# Run pytest with verbose output
python -m pytest test_server.py -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed! You're good to go to work! 🎉"
    exit 0
else
    echo ""
    echo "❌ Some tests failed. Please fix them before proceeding."
    exit 1
fi
