#!/bin/bash

# Base directory
PLUGIN_DIR="./strom-tarif-plugin"
BASE_NAME="strom-tarif-plugin"
PHP_FILE="${PLUGIN_DIR}/strom-tarif-plugin.php"

# Get current version from PHP file
CURRENT_VERSION=$(grep "Version:" "$PHP_FILE" | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+")
echo "Current version: $CURRENT_VERSION"

# Split version into components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Increment version
if [ "$PATCH" -eq 9 ]; then
    PATCH=0
    MINOR=$((MINOR + 1))
else
    PATCH=$((PATCH + 1))
fi

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "New version: $NEW_VERSION"

# Create a temporary file with the updated version
awk -v new_ver="$NEW_VERSION" '{
    if ($0 ~ /\* Version:/) {
        gsub(/[0-9]+\.[0-9]+\.[0-9]+/, new_ver);
    }
    print;
}' "$PHP_FILE" > "${PHP_FILE}.tmp"

# Replace the original file with the updated one
mv "${PHP_FILE}.tmp" "$PHP_FILE"

# Verify the update
UPDATED_VERSION=$(grep "Version:" "$PHP_FILE" | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+")
echo "Updated version in file: $UPDATED_VERSION"

# Create zip file
zip -r "${BASE_NAME}_v${NEW_VERSION}.zip" "$PLUGIN_DIR" -x "*.DS_Store" -x "*.git*"

echo "Created ${BASE_NAME}_v${NEW_VERSION}.zip"