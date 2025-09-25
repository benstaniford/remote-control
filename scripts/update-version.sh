#!/bin/bash
# Bash script to update version information in AssemblyInfo.cs
# Usage: ./update-version.sh v0.1.4

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v0.1.4"
    exit 1
fi

VERSION="$1"
# Remove 'v' prefix if present
CLEAN_VERSION="${VERSION#v}"

# Split version into parts
IFS='.' read -ra VERSION_PARTS <<< "$CLEAN_VERSION"

if [ ${#VERSION_PARTS[@]} -lt 3 ]; then
    echo "Error: Version must be in format 'major.minor.patch' (e.g., '0.1.4')"
    exit 1
fi

MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"
BUILD_VERSION="${MAJOR}.${MINOR}.${PATCH}.0"

ASSEMBLY_INFO_PATH="RemoteControlApp/Properties/AssemblyInfo.cs"

if [ ! -f "$ASSEMBLY_INFO_PATH" ]; then
    echo "Error: AssemblyInfo.cs not found at: $ASSEMBLY_INFO_PATH"
    exit 1
fi

echo "Updating version to: $VERSION"
echo "Assembly version: $BUILD_VERSION"

# Update AssemblyVersion
sed -i "s/\[assembly: AssemblyVersion(\".*\")\]/[assembly: AssemblyVersion(\"$BUILD_VERSION\")]/" "$ASSEMBLY_INFO_PATH"

# Update AssemblyFileVersion  
sed -i "s/\[assembly: AssemblyFileVersion(\".*\")\]/[assembly: AssemblyFileVersion(\"$BUILD_VERSION\")]/" "$ASSEMBLY_INFO_PATH"

# Update AssemblyInformationalVersion with the git tag
sed -i "s/\[assembly: AssemblyInformationalVersion(\".*\")\]/[assembly: AssemblyInformationalVersion(\"$VERSION\")]/" "$ASSEMBLY_INFO_PATH"

echo "AssemblyInfo.cs updated successfully"

# Also update the WiX installer version
WIX_PATH="RemoteControlInstaller/Product.wxs"
if [ -f "$WIX_PATH" ]; then
    echo "Updating WiX installer version..."
    sed -i "s/Version=\".*\"/Version=\"$BUILD_VERSION\"/" "$WIX_PATH"
    echo "WiX installer version updated"
else
    echo "Warning: WiX file not found at: $WIX_PATH"
fi