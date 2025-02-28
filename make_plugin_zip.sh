#!/bin/bash

# Base directory
PLUGIN_DIR="./strom-tarif-plugin"
BASE_NAME="strom-tarif-plugin"

# Find the latest version number
LATEST_VERSION=$(ls ${BASE_NAME}_v*.zip 2>/dev/null | grep -o "v[0-9]\+\.[0-9]\+" | sort -V | tail -n1)

if [ -z "$LATEST_VERSION" ]; then
    NEW_VERSION="v1.0"
else
    MAJOR=$(echo $LATEST_VERSION | cut -d. -f1 | tr -d 'v')
    MINOR=$(echo $LATEST_VERSION | cut -d. -f2)
    MINOR=$((MINOR + 1))
    NEW_VERSION="v${MAJOR}.${MINOR}"
fi

# Create zip file
zip -r "${BASE_NAME}_${NEW_VERSION}.zip" "$PLUGIN_DIR" -x "*.DS_Store" -x "*.git*"

echo "Created ${BASE_NAME}_${NEW_VERSION}.zip"