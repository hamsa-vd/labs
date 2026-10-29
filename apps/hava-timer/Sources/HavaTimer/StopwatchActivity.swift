import AppKit

enum StopwatchActivityPolicy {
    static func shouldPulse(idleFor: TimeInterval, mouseButtonDown: Bool,
                            modifierDown: Bool, screenAwake: Bool) -> Bool {
        idleFor.isFinite && idleFor >= 55 && !mouseButtonDown && !modifierDown && screenAwake
    }
}

@MainActor
final class StopwatchActivity {
    private var ticker: Timer?
    var isScheduled: Bool { ticker != nil }
    var hasPermission: Bool { CGPreflightPostEventAccess() }

    func update(running: Bool, enabled: Bool) {
        let shouldRun = running && enabled
        guard shouldRun != isScheduled else { return }
        stop()
        guard shouldRun else { return }
        let timer = Timer(timeInterval: 60, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.pulseIfIdle() }
        }
        ticker = timer
        RunLoop.main.add(timer, forMode: .common)
    }

    func stop() {
        ticker?.invalidate()
        ticker = nil
    }

    // Called only by a deliberate user click in the menu; never silently
    // requests persistent input-control permission when a stopwatch starts.
    func requestPermission() { _ = CGRequestPostEventAccess() }

    private func pulseIfIdle() {
        guard isScheduled, hasPermission else { return }
        let types: [CGEventType] = [.mouseMoved, .keyDown, .leftMouseDown, .rightMouseDown,
                                   .scrollWheel, .flagsChanged, .leftMouseDragged, .rightMouseDragged]
        let idle = types.map { CGEventSource.secondsSinceLastEventType(.combinedSessionState, eventType: $0) }.min() ?? 0
        let buttons: [CGMouseButton] = [.left, .right, .center]
        let buttonDown = buttons.contains { CGEventSource.buttonState(.combinedSessionState, button: $0) }
        let modifiers = CGEventSource.flagsState(.combinedSessionState)
            .intersection([.maskCommand, .maskControl, .maskAlternate, .maskShift])
        let foreground = NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? ""
        let awake = CGDisplayIsAsleep(CGMainDisplayID()) == 0
            && foreground != "com.apple.loginwindow" && !foreground.lowercased().contains("screensaver")
        guard StopwatchActivityPolicy.shouldPulse(idleFor: idle, mouseButtonDown: buttonDown,
                                                   modifierDown: !modifiers.isEmpty, screenAwake: awake),
              let original = CGEvent(source: nil)?.location,
              let source = CGEventSource(stateID: .hidSystemState) else { return }
        // These remain generated events, not real hardware events. Do not type
        // keys, click controls, switch apps or modify Teams' presence directly.
        source.localEventsSuppressionInterval = 0
        source.userData = 0x48415641
        let displayFrame = NSScreen.screens.compactMap { screen -> CGRect? in
            guard let id = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber else { return nil }
            return CGDisplayBounds(id.uint32Value)
        }.first { $0.contains(original) }
        guard let displayFrame else { return }
        let nudged = CGPoint(x: original.x + (original.x + 1 < displayFrame.maxX ? 1 : -1), y: original.y)
        guard let out = CGEvent(mouseEventSource: source, mouseType: .mouseMoved,
                                 mouseCursorPosition: nudged, mouseButton: .left),
              let back = CGEvent(mouseEventSource: source, mouseType: .mouseMoved,
                                  mouseCursorPosition: original, mouseButton: .left) else { return }
        out.post(tap: .cghidEventTap)
        back.post(tap: .cghidEventTap)
    }
}
