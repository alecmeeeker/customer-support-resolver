#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="Limrose"
BUNDLE_ID="com.applequist.limrose"
VERSION="1.0.0"
DIST_DIR="$SCRIPT_DIR/dist"

echo "Building $APP_NAME.app..."

# Build release binary
swift build -c release 2>&1

# Get the binary path
BINARY=$(swift build -c release --show-bin-path)/$APP_NAME
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found at $BINARY"
    exit 1
fi

# Clean dist
rm -rf "$DIST_DIR/$APP_NAME.app"
mkdir -p "$DIST_DIR"

# Create .app bundle structure
APP_DIR="$DIST_DIR/$APP_NAME.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy binary
cp "$BINARY" "$APP_DIR/Contents/MacOS/$APP_NAME"

# Generate Info.plist
cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>Limrose Customer Dashboard</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright 2024 Alec Meeker and Applequist Inc.</string>
</dict>
</plist>
PLIST

# Generate PkgInfo
echo -n "APPL????" > "$APP_DIR/Contents/PkgInfo"

echo ""
echo "Build complete!"
echo "App bundle: $DIST_DIR/$APP_NAME.app"
echo "Size: $(du -sh "$APP_DIR" | cut -f1)"
echo ""
echo "To run:  open $DIST_DIR/$APP_NAME.app"
echo "To zip:  cd $DIST_DIR && zip -r $APP_NAME.zip $APP_NAME.app"
