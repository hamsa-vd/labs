# MarkdownViewer

MarkdownViewer is a lightweight macOS app that renders `.md` and `.markdown` files as formatted content using SwiftUI and WebKit.

## Features

- Open markdown files via the toolbar or drag and drop.
- Rendered preview with offline CSS/JS assets.
- Mermaid diagram rendering for fenced code blocks.
- Zoom controls and appearance override (system, light, dark).
- Panel and window opacity controls.

## Requirements

- macOS 13 or later
- Xcode (recent version that supports macOS 13 deployment)

## Build and Run

1. Clone this repository.
2. Open `MarkdownViewer.xcodeproj` in Xcode.
3. Select the `MarkdownViewer` scheme and a `My Mac` destination.
4. Build and run.

## Quick Look Status

Quick Look integration is implemented via a Quick Look Preview extension target. Build the app in Xcode, then use Finder Spacebar preview on `.md` files. If the preview does not appear immediately, restart Quick Look or re-register the app.
