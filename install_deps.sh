#!/bin/bash
set -e

echo "Installing LazyKube dependencies..."
pip install -r requirements.txt
echo "Done! Run with: python lazykube.py"
