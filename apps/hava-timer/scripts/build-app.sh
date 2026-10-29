#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! swift --version >/dev/null 2>&1 && [ -d /Library/Developer/CommandLineTools ]; then
  export DEVELOPER_DIR=/Library/Developer/CommandLineTools
fi
if [ -f timer.svg ]; then
  cp timer.svg Sources/HavaTimer/Resources/timer.svg
fi
swift build -c release
BIN_DIR="$(swift build -c release --show-bin-path)"
APP="dist/hava timer.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp Sources/HavaTimer/Resources/Sora.ttf Sources/HavaTimer/Resources/Sora-OFL.txt "$APP/Contents/Resources/"
cp Sources/HavaTimer/Resources/timer.svg "$APP/Contents/Resources/"
cp "$BIN_DIR/hava-timer" "$APP/Contents/MacOS/hava-timer"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>hava-timer</string>
  <key>CFBundleIdentifier</key><string>local.hava-timer</string>
  <key>CFBundleName</key><string>hava timer</string>
  <key>CFBundleDisplayName</key><string>hava timer</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.12.0</string>
  <key>CFBundleVersion</key><string>29</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>LSUIElement</key><true/>
  <key>CFBundleURLTypes</key><array><dict>
    <key>CFBundleURLName</key><string>local.hava-timer.start</string>
    <key>CFBundleURLSchemes</key><array><string>hava-timer</string></array>
  </dict></array>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - "$APP"
echo "Built $APP"
