import AppKit

enum WallClockText {
    // Read the current calendar/time zone on every update, including after wake
    // or a system time-zone change. Always show hours, minutes and seconds.
    static func format(_ date: Date, calendar: Calendar = .autoupdatingCurrent) -> String {
        let parts = calendar.dateComponents([.hour, .minute, .second], from: date)
        return String(format: "%02d:%02d:%02d", parts.hour ?? 0, parts.minute ?? 0, parts.second ?? 0)
    }
}

enum ClockPlacement {
    static func origin(corner: Corner, frame: NSRect, size: NSSize) -> NSPoint {
        let usable = frame.insetBy(dx: 2, dy: 2)
        let left = corner == .topLeft || corner == .bottomLeft
        let top = corner == .topLeft || corner == .topRight
        return NSPoint(x: left ? usable.minX : usable.maxX - size.width,
                       y: top ? usable.maxY - size.height : usable.minY)
    }

    static func nearest(center: NSPoint, frame: NSRect, size: NSSize) -> Corner {
        let corners: [Corner] = [.topRight, .bottomRight, .bottomLeft, .topLeft]
        return corners.min {
            let a = origin(corner: $0, frame: frame, size: size)
            let b = origin(corner: $1, frame: frame, size: size)
            return hypot(a.x + size.width / 2 - center.x, a.y + size.height / 2 - center.y)
                < hypot(b.x + size.width / 2 - center.x, b.y + size.height / 2 - center.y)
        } ?? .topRight
    }
}

@MainActor
final class WallClockDisplays: NSObject {
    @MainActor
    private final class Display {
        let id: UInt32
        let panel: OverlayPanel
        let numbers: NumbersView
        var screen: NSScreen
        var corner: Corner
        var snap: Task<Void, Never>?

        init(id: UInt32, screen: NSScreen) {
            self.id = id
            self.screen = screen
            corner = Corner(rawValue: UserDefaults.standard.string(forKey: "clockCorner-\(id)") ?? "") ?? .topRight
            numbers = NumbersView(frame: NSRect(x: 0, y: 0, width: 250, height: 66))
            numbers.showsSymbol = false
            numbers.steadyGlow = 0.7
            panel = OverlayPanel(contentRect: numbers.frame, styleMask: [.borderless, .nonactivatingPanel],
                                 backing: .buffered, defer: false)
            panel.title = "Hava Clock"
            panel.level = .statusBar
            panel.isFloatingPanel = true
            panel.becomesKeyOnlyIfNeeded = true
            panel.worksWhenModal = true
            panel.hidesOnDeactivate = false
            panel.isReleasedWhenClosed = false
            panel.isOpaque = false
            panel.backgroundColor = NSColor.black.withAlphaComponent(0.02)
            panel.hasShadow = false
            panel.ignoresMouseEvents = false
            panel.acceptsMouseMovedEvents = true
            panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
            panel.contentView = numbers
            numbers.setAccessibilityElement(true)
            numbers.setAccessibilityRole(.staticText)
        }

        func close() {
            snap?.cancel()
            panel.orderOut(nil)
            panel.close()
        }
    }

    private var displays: [UInt32: Display] = [:]
    private var ticker: Timer?
    private let openMenu: () -> Void
    private let disable: () -> Void

    init(openMenu: @escaping () -> Void, disable: @escaping () -> Void) {
        self.openMenu = openMenu
        self.disable = disable
        super.init()
    }

    func show() {
        reconcileScreens()
        ticker?.invalidate()
        let timer = Timer(timeInterval: 0.2, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.update() }
        }
        ticker = timer
        RunLoop.main.add(timer, forMode: .common)
    }

    func hide() {
        ticker?.invalidate()
        ticker = nil
        displays.values.forEach { $0.close() }
        displays.removeAll()
    }

    private func screenID(_ screen: NSScreen) -> UInt32? {
        (screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value
    }

    func reconcileScreens() {
        let screens = NSScreen.screens
        let activeIDs = Set(screens.compactMap { screenID($0) })
        for id in displays.keys.filter({ !activeIDs.contains($0) }) {
            displays.removeValue(forKey: id)?.close()
        }
        for screen in screens {
            guard let id = screenID(screen) else { continue }
            if let existing = displays[id] {
                existing.screen = screen
                if !existing.numbers.isDragging { place(existing) }
                continue
            }
            let display = Display(id: id, screen: screen)
            displays[id] = display
            display.numbers.onPickUp = { [weak display] in
                display?.snap?.cancel()
                display?.snap = nil
            }
            display.numbers.onDrop = { [weak self, weak display] _ in
                guard let display else { return }
                self?.snap(display)
            }
            display.numbers.onConfigure = { [weak self] in self?.openMenu() }
            display.numbers.contextMenu = { [weak self] in self?.makeMenu() ?? NSMenu() }
            display.numbers.text = WallClockText.format(Date())
            place(display)
        }
        update()
    }

    private func update(forceOrdering: Bool = false) {
        let menuBars = MenuBarVisibility.snapshot()
        // Use one timestamp for all monitors so their seconds always agree.
        let text = WallClockText.format(Date())
        for display in displays.values {
            let size = display.panel.frame.size
            display.numbers.text = text
            display.numbers.setAccessibilityLabel("Hava Clock, current time \(text)")
            if size != display.panel.frame.size, !display.numbers.isDragging, display.snap == nil {
                place(display)
            }
            // Do not take an actively dragged clock away from the pointer.
            guard !display.numbers.isDragging else { continue }
            let menuVisible = MenuBarVisibility.visible(on: display.screen.frame,
                windows: menuBars.windows, fallback: menuBars.fallback)
            if menuVisible {
                display.snap?.cancel()
                display.snap = nil
                if display.panel.isVisible { display.panel.orderOut(nil) }
            } else if !display.panel.isVisible || forceOrdering {
                place(display)
                display.panel.orderFrontRegardless()
            }
        }
    }

    func bringForward() {
        update(forceOrdering: true)
    }

    private func place(_ display: Display) {
        guard !display.numbers.isDragging else { return }
        display.panel.setFrameOrigin(ClockPlacement.origin(corner: display.corner,
            frame: display.screen.visibleFrame, size: display.panel.frame.size))
    }

    private func snap(_ display: Display) {
        display.snap?.cancel()
        // Each monitor keeps its own clock, even if dragged across a boundary.
        display.corner = ClockPlacement.nearest(center: NSPoint(x: display.panel.frame.midX, y: display.panel.frame.midY),
            frame: display.screen.visibleFrame, size: display.panel.frame.size)
        UserDefaults.standard.set(display.corner.rawValue, forKey: "clockCorner-\(display.id)")
        guard !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion else { place(display); return }
        let start = display.panel.frame.origin
        let end = ClockPlacement.origin(corner: display.corner, frame: display.screen.visibleFrame,
                                        size: display.panel.frame.size)
        display.snap = Task { @MainActor [weak self, weak display] in
            guard let self, let display else { return }
            for step in 1...20 {
                do { try await Task.sleep(nanoseconds: 16_000_000) } catch { return }
                guard !Task.isCancelled, !display.numbers.isDragging else { return }
                let eased = CGFloat(1 - pow(1 - Double(step) / 20, 3))
                display.panel.setFrameOrigin(NSPoint(x: start.x + (end.x - start.x) * eased,
                                                      y: start.y + (end.y - start.y) * eased))
            }
            display.snap = nil
            self.place(display)
        }
    }

    private func makeMenu() -> NSMenu {
        let menu = NSMenu()
        let hide = NSMenuItem(title: "Hide Hava Clock", action: #selector(hideFromMenu), keyEquivalent: "")
        hide.target = self
        menu.addItem(hide)
        menu.addItem(.separator())
        let quit = NSMenuItem(title: "Quit hava timer", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        quit.target = NSApp
        menu.addItem(quit)
        return menu
    }

    @objc private func hideFromMenu() { disable() }
}
