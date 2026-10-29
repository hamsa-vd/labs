import AppKit

@MainActor
final class ScreenBorderView: NSView {
    var intensity: CGFloat = 0 { didSet { needsDisplay = true } }

    override func draw(_ dirtyRect: NSRect) {
        guard intensity > 0, let context = NSGraphicsContext.current?.cgContext else { return }
        let rect = bounds.insetBy(dx: 7, dy: 7)
        let path = CGPath(roundedRect: rect, cornerWidth: 18, cornerHeight: 18, transform: nil)
        context.saveGState()
        // Glow stays at the edges; the center of the screen remains untouched.
        context.setShadow(offset: .zero, blur: 22,
                          color: NSColor.white.withAlphaComponent(0.85 * intensity).cgColor)
        context.addPath(path)
        context.setStrokeColor(NSColor.white.withAlphaComponent(0.25 * intensity).cgColor)
        context.setLineWidth(10)
        context.strokePath()
        context.setShadow(offset: .zero, blur: 7,
                          color: NSColor.white.withAlphaComponent(intensity).cgColor)
        context.addPath(path)
        context.setStrokeColor(NSColor.white.withAlphaComponent(0.95 * intensity).cgColor)
        context.setLineWidth(3)
        context.strokePath()
        context.restoreGState()
    }
}

@MainActor
final class ScreenCompletionBorder {
    private let window: OverlayPanel
    private let border: ScreenBorderView

    init?(screen: NSScreen?) {
        guard let screen else { return nil }
        border = ScreenBorderView(frame: NSRect(origin: .zero, size: screen.frame.size))
        window = OverlayPanel(contentRect: screen.frame,
            styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = false
        window.hidesOnDeactivate = false
        window.isReleasedWhenClosed = false
        window.ignoresMouseEvents = true
        window.level = NSWindow.Level(rawValue: NSWindow.Level.statusBar.rawValue + 1)
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        window.contentView = border
        window.orderFrontRegardless()
    }

    func setGlow(_ intensity: CGFloat) { border.intensity = intensity }
    func bringForward() { window.orderFrontRegardless() }

    func move(to screen: NSScreen?) {
        guard let screen else { return }
        window.setFrame(screen.frame, display: true)
        border.frame = NSRect(origin: .zero, size: screen.frame.size)
    }

    func dismiss() {
        window.orderOut(nil)
        window.close()
    }
}
