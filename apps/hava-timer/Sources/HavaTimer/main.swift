import AppKit
import Combine
import QuartzCore
import CoreText

enum Corner: String {
    case topRight, bottomRight, bottomLeft, topLeft
}

enum TimerTint {
    case neutral, red

    static func current(remaining: TimeInterval, duration: TimeInterval) -> TimerTint {
        guard duration > 0 else { return .neutral }
        if remaining < duration * 0.1 { return .red }
        return .neutral
    }

    var color: NSColor {
        switch self {
        case .neutral: return .white
        case .red: return NSColor.systemRed.blended(withFraction: 0.55, of: .white) ?? .systemRed
        }
    }
}

enum TimerText {
    static func format(_ remaining: TimeInterval) -> String {
        let seconds = max(0, Int(ceil(remaining)))
        return seconds >= 3600
            ? String(format: "%d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60)
            : String(format: "%d:%02d", seconds / 60, seconds % 60)
    }
}

enum TimerTypography {
    static let digits: NSFont = {
        // Register only for this process; no system font installation is needed.
        let url = Bundle.main.url(forResource: "Sora", withExtension: "ttf")
            ?? Bundle.module.url(forResource: "Sora", withExtension: "ttf")
        if let url { CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil) }
        let features: [[NSFontDescriptor.FeatureKey: Int]] = [[
            .typeIdentifier: kNumberSpacingType,
            .selectorIdentifier: kMonospacedNumbersSelector
        ]]
        let descriptor = NSFontDescriptor(fontAttributes: [
            .name: "Sora-Regular",
            .variation: [NSNumber(value: 0x77676874): NSNumber(value: 700)],
            .featureSettings: features
        ])
        return NSFont(descriptor: descriptor, size: 42)
            ?? NSFont.monospacedDigitSystemFont(ofSize: 42, weight: .bold)
    }()
    static func outline(for text: String) -> CGPath {
        let line = CTLineCreateWithAttributedString(NSAttributedString(string: text, attributes: [.font: digits]))
        let runs = CTLineGetGlyphRuns(line) as! [CTRun]
        let characters = Array(text.utf16)
        let numbers = CGMutablePath()
        var colons: [CGPath] = []
        for run in runs {
            let count = CTRunGetGlyphCount(run)
            var glyphs = [CGGlyph](repeating: 0, count: count)
            var positions = [CGPoint](repeating: .zero, count: count)
            var indices = [CFIndex](repeating: 0, count: count)
            CTRunGetGlyphs(run, CFRange(location: 0, length: 0), &glyphs)
            CTRunGetPositions(run, CFRange(location: 0, length: 0), &positions)
            CTRunGetStringIndices(run, CFRange(location: 0, length: 0), &indices)
            let font = (CTRunGetAttributes(run) as NSDictionary)[kCTFontAttributeName] as! CTFont
            for index in 0..<count {
                guard let glyph = CTFontCreatePathForGlyph(font, glyphs[index], nil) else { continue }
                var placement = CGAffineTransform(translationX: positions[index].x, y: positions[index].y)
                let placed = glyph.copy(using: &placement)!
                if characters.indices.contains(indices[index]), characters[indices[index]] == 58 {
                    colons.append(placed)
                } else { numbers.addPath(placed) }
            }
        }
        let centerY = numbers.boundingBoxOfPath.midY
        for colon in colons {
            numbers.addPath(colon, transform: CGAffineTransform(translationX: 0,
                y: centerY - colon.boundingBoxOfPath.midY))
        }
        return numbers.normalized(using: .winding)
    }

}

enum TimerMode {
    case countdown, stopwatch
}

@MainActor
final class TimerModel: ObservableObject {
    @Published var minutes: Double = 25
    // Displayed time: remaining in countdown mode, elapsed in stopwatch mode.
    @Published private(set) var remaining: TimeInterval = 25 * 60
    @Published private(set) var running = false
    @Published private(set) var hasStarted = false
    @Published private(set) var finished = false
    private(set) var mode: TimerMode = .countdown
    private(set) var duration: TimeInterval = 0
    private let now: () -> Date
    private var deadline: Date?
    private var stopwatchStartedAt: Date?
    private var elapsedBeforeResume: TimeInterval = 0
    private var ticker: Timer?
    var showOverlay: (() -> Void)?
    var onComplete: (() -> Void)?
    var onReset: (() -> Void)?

    init(now: @escaping () -> Date = Date.init) { self.now = now }

    var display: String {
        TimerText.format(mode == .stopwatch ? floor(remaining) : remaining)
    }
    var validDuration: Bool { minutes.isFinite && minutes >= 1 && minutes <= 1440 }
    var canResume: Bool { hasStarted && !finished && (mode == .stopwatch || remaining > 0) }

    func start() {
        guard validDuration else { return }
        clearClock()
        mode = .countdown
        duration = (minutes * 60).rounded()
        finished = false
        hasStarted = true
        remaining = duration
        resume()
        showOverlay?()
    }

    func canAddTime(_ seconds: TimeInterval) -> Bool {
        mode == .countdown && hasStarted && !finished && remaining > 0
            && seconds.isFinite && seconds > 0 && duration + seconds <= 1440 * 60
    }

    func addTime(_ seconds: TimeInterval) {
        guard canAddTime(seconds) else { return }
        let date = now()
        let current = running ? max(0, deadline?.timeIntervalSince(date) ?? remaining) : remaining
        guard current > 0 else { refresh(); return }
        duration += seconds
        minutes = duration / 60
        if running { deadline = date.addingTimeInterval(current + seconds) }
        // Preserve the running/paused state and refresh the tint and display.
        remaining = current + seconds
    }

    func startStopwatch() {
        clearClock()
        mode = .stopwatch
        duration = 0
        finished = false
        hasStarted = true
        remaining = 0
        resume()
        showOverlay?()
    }

    private func clearClock() {
        ticker?.invalidate()
        ticker = nil
        running = false
        deadline = nil
        stopwatchStartedAt = nil
        elapsedBeforeResume = 0
    }

    func pause() {
        refresh()
        if mode == .stopwatch { elapsedBeforeResume = remaining }
        deadline = nil
        stopwatchStartedAt = nil
        running = false
        ticker?.invalidate()
        ticker = nil
    }

    func resume() {
        guard !running, canResume else { return }
        if mode == .stopwatch { stopwatchStartedAt = now() }
        else { deadline = now().addingTimeInterval(remaining) }
        running = true
        let timer = Timer(timeInterval: 0.1, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.refresh() }
        }
        ticker = timer
        RunLoop.main.add(timer, forMode: .common)
    }

    func reset() {
        if mode == .stopwatch {
            clearClock()
            hasStarted = true
            finished = false
            duration = 0
            remaining = 0
            showOverlay?()
        } else { stop() }
    }

    func stop() {
        clearClock()
        hasStarted = false
        finished = false
        duration = 0
        remaining = mode == .stopwatch ? 0 : (validDuration ? (minutes * 60).rounded() : 0)
        onReset?()
    }

    private func refresh() {
        if mode == .stopwatch {
            guard let stopwatchStartedAt else { return }
            remaining = elapsedBeforeResume + max(0, now().timeIntervalSince(stopwatchStartedAt))
            return
        }
        guard let deadline else { return }
        remaining = max(0, deadline.timeIntervalSince(now()))
        if remaining == 0 {
            self.deadline = nil
            running = false
            finished = true
            ticker?.invalidate()
            ticker = nil
            NSSound.beep()
            onComplete?()
        }
    }
}

// Custom duration lives in a small popover anchored to the menu bar,
// rather than a separate application window.
@MainActor
final class DurationEditor: NSViewController {
    let input = NSTextField()
    private let hint = NSTextField(labelWithString: "Choose 1–1,440 minutes.")
    var onStart: ((Double) -> Void)?
    var onCancel: (() -> Void)?
    var minutes: Double = 25

    override func loadView() {
        view = NSView(frame: NSRect(x: 0, y: 0, width: 288, height: 140))
        let title = NSTextField(labelWithString: "Custom timer")
        title.font = .boldSystemFont(ofSize: 14)
        title.frame = NSRect(x: 16, y: 108, width: 256, height: 20)
        input.frame = NSRect(x: 16, y: 72, width: 104, height: 24)
        input.stringValue = String(format: "%g", minutes)
        input.placeholderString = "Minutes"
        input.setAccessibilityLabel("Duration in minutes")
        input.target = self
        input.action = #selector(start)
        let unit = NSTextField(labelWithString: "minutes")
        unit.frame = NSRect(x: 130, y: 75, width: 100, height: 20)
        hint.font = .systemFont(ofSize: 11)
        hint.textColor = .secondaryLabelColor
        hint.frame = NSRect(x: 16, y: 48, width: 256, height: 18)
        let start = NSButton(title: "Start timer", target: self, action: #selector(start))
        start.bezelStyle = .rounded
        start.keyEquivalent = "\r"
        start.frame = NSRect(x: 160, y: 10, width: 112, height: 30)
        let cancel = NSButton(title: "Cancel", target: self, action: #selector(cancel))
        cancel.bezelStyle = .rounded
        cancel.keyEquivalent = "\u{1b}"
        cancel.frame = NSRect(x: 72, y: 10, width: 80, height: 30)
        for child in [title, input, unit, hint, start, cancel] { view.addSubview(child) }
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        view.window?.makeKey()
        view.window?.makeFirstResponder(input)
        input.selectText(nil)
    }

    @objc private func start() {
        let value = input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let minutes = Double(value), minutes.isFinite, (1...1440).contains(minutes) else {
            hint.stringValue = "Enter a number from 1 to 1,440."
            hint.textColor = .systemRed
            return
        }
        onStart?(minutes)
    }

    @objc private func cancel() { onCancel?() }
}

// Handle the complete drag ourselves: a release always ends with corner snapping,
// including releases outside the window or in the middle of another display.
@MainActor
final class NumbersView: NSView {
    var text = "25:00" { didSet {
        if text != oldValue { cachedTextOutline = nil; cachedOutline = nil; updateGlass(); needsDisplay = true }
    } }
    var showsSymbol = true {
        didSet {
            guard showsSymbol != oldValue else { return }
            cachedOutline = nil
            updateGlass()
            needsDisplay = true
        }
    }
    var tint: TimerTint = .neutral {
        didSet {
            guard tint != oldValue else { return }
            updateGlass()
            needsDisplay = true
        }
    }
    // During completion the pulse takes precedence over hover highlighting.
    var completionGlow: CGFloat? {
        didSet { updateGlass(); needsDisplay = true }
    }
    var urgencyGlow: CGFloat? {
        didSet {
            if (oldValue == nil) != (urgencyGlow == nil) { refreshUrgencyAnimation() }
            updateGlass()
            needsDisplay = true
        }
    }
    var steadyGlow: CGFloat = 0 {
        didSet {
            guard steadyGlow != oldValue else { return }
            updateGlass()
            needsDisplay = true
        }
    }
    private var glowStrength: CGFloat {
        completionGlow ?? max(steadyGlow, max(urgencyGlow ?? 0, hovered ? 1 : 0))
    }
    // Highlighting always uses neutral glass and white light, even during
    // the final red phase. Keep all three completion pulses neutral.
    private var appearanceTint: TimerTint {
        completionGlow != nil || hovered ? .neutral : (urgencyGlow != nil ? .red : tint)
    }
    private var glowColor: NSColor {
        if urgencyGlow != nil && completionGlow == nil && !hovered { return .systemRed }
        return appearanceTint.color
    }
    private(set) var isDragging = false
    var onPickUp: (() -> Void)?
    var onDrop: ((NSPoint) -> Void)?
    var onConfigure: (() -> Void)?
    var contextMenu: (() -> NSMenu)?
    var handAngle: CGFloat = 0 {
        didSet {
            guard handAngle != oldValue else { return }
            cachedOutline = nil
            updateGlass()
            needsDisplay = true
        }
    }
    private var cachedTextOutline: CGPath?
    private var cachedOutline: CGPath?
    private var glass: NSView?
    private let gradientView = NSView()
    private let redGradient = CAGradientLayer()
    private let darkRed = NSColor(calibratedRed: 0.56, green: 0.05, blue: 0.10, alpha: 1)
    private let lightRed = NSColor(calibratedRed: 1, green: 0.66, blue: 0.62, alpha: 1)
    private var hoverArea: NSTrackingArea?
    private var hovered = false {
        didSet {
            guard hovered != oldValue else { return }
            updateGlass()
            needsDisplay = true
        }
    }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let hoverArea { removeTrackingArea(hoverArea) }
        let area = NSTrackingArea(rect: .zero,
            options: [.mouseEnteredAndExited, .mouseMoved, .activeAlways, .inVisibleRect],
            owner: self, userInfo: nil)
        addTrackingArea(area)
        hoverArea = area
    }

    override func mouseEntered(with event: NSEvent) { hovered = true; NSCursor.openHand.set() }
    override func mouseMoved(with event: NSEvent) { hovered = true; NSCursor.openHand.set() }
    override func mouseExited(with event: NSEvent) { hovered = false; NSCursor.arrow.set() }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        if #available(macOS 26.0, *) {
            let effect = NSGlassEffectView(frame: bounds)
            effect.style = .clear
            effect.tintColor = NSColor.white.withAlphaComponent(0.4)
            effect.wantsLayer = true
            addSubview(effect)
            glass = effect
            gradientView.wantsLayer = true
            gradientView.layer = redGradient
            redGradient.colors = [darkRed.cgColor, lightRed.cgColor]
            redGradient.startPoint = CGPoint(x: 0, y: 0)
            redGradient.endPoint = CGPoint(x: 1, y: 1)
            addSubview(gradientView)
        }
        updateGlass()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    // The overlay belongs to an inactive accessory app. Accept the very first
    // press so dragging never requires activating the app beforehand.
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
    override var needsPanelToBecomeKey: Bool { false }

    override func hitTest(_ point: NSPoint) -> NSView? {
        // NSView hit-test points arrive in the superview's coordinate system.
        let local = superview.map { convert(point, from: $0) } ?? point
        return bounds.contains(local) ? self : nil
    }

    override func resetCursorRects() {
        addCursorRect(bounds, cursor: .openHand)
    }

    private func glyphPath() -> CGPath {
        if let cachedOutline { return cachedOutline }
        let path = cachedTextOutline ?? TimerTypography.outline(for: text)
        cachedTextOutline = path
        let textBox = path.boundingBox
        let iconWidth = showsSymbol ? textBox.height * TimerSymbol.aspectRatio : 0
        let combined = CGMutablePath()
        if showsSymbol {
            combined.addPath(TimerSymbol.path(in: NSRect(x: textBox.minX, y: textBox.minY,
                width: iconWidth, height: textBox.height), handAngle: handAngle))
        }
        combined.addPath(path, transform: CGAffineTransform(translationX: showsSymbol ? iconWidth + 8 : 0, y: 0))
        let box = combined.boundingBox
        // Size the window to the ink, eliminating the previous invisible side padding.
        let size = NSSize(width: ceil(box.width) + 8, height: ceil(box.height) + 8)
        if !isDragging && frame.size != size { setFrameSize(size); window?.setContentSize(size) }
        var transform = CGAffineTransform(translationX: 4 - box.minX, y: 4 - box.minY)
        // Variable-font glyphs contain overlapping component contours. Merge
        // their filled regions before outlining, avoiding internal square seams.
        let outline = combined.copy(using: &transform)!.normalized(using: .winding)
        cachedOutline = outline
        return outline
    }

    func bounce() {
        guard !isDragging else { return }
        guard !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion else { return }
        let animation = CAKeyframeAnimation(keyPath: "transform")
        animation.values = [
            NSValue(caTransform3D: CATransform3DIdentity),
            NSValue(caTransform3D: CATransform3DMakeScale(1.02, 0.96, 1)),
            NSValue(caTransform3D: CATransform3DMakeScale(0.99, 1.035, 1)),
            NSValue(caTransform3D: CATransform3DMakeScale(1.005, 0.99, 1)),
            NSValue(caTransform3D: CATransform3DIdentity)
        ]
        animation.keyTimes = [0, 0.22, 0.52, 0.78, 1]
        animation.duration = 0.45
        animation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        glass?.layer?.add(animation, forKey: "minuteBounce")
        gradientView.layer?.add(animation, forKey: "minuteBounce")
    }

    private func refreshUrgencyAnimation() {
        glass?.layer?.removeAnimation(forKey: "urgencyPulse")
        gradientView.layer?.removeAnimation(forKey: "urgencyPulse")
        guard urgencyGlow != nil, !isDragging,
              !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion else { return }
        let pulse = CAKeyframeAnimation(keyPath: "transform.scale")
        pulse.values = [1, 1.018, 1]
        pulse.keyTimes = [0, 0.5, 1]
        pulse.duration = 1
        pulse.repeatCount = .infinity
        pulse.timingFunctions = [CAMediaTimingFunction(name: .easeInEaseOut),
                                 CAMediaTimingFunction(name: .easeInEaseOut)]
        glass?.layer?.add(pulse, forKey: "urgencyPulse")
        gradientView.layer?.add(pulse, forKey: "urgencyPulse")
    }

    private func updateGlass() {
        let path = glyphPath()
        guard let glass else { return }
        glass.frame = bounds
        // Tint the glyphs diagonally from dark red to light red, preserving
        // the native glass refraction underneath rather than replacing it.
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        gradientView.frame = bounds
        redGradient.opacity = appearanceTint == .red ? 0.55 : 0
        let gradientMask = CAShapeLayer()
        gradientMask.frame = bounds
        gradientMask.path = path
        redGradient.mask = gradientMask
        CATransaction.commit()
        if #available(macOS 26.0, *), let effect = glass as? NSGlassEffectView {
            effect.tintColor = appearanceTint.color.withAlphaComponent(0.4 + 0.4 * glowStrength)
        }
        let mask = CAShapeLayer()
        mask.frame = bounds
        mask.path = path
        glass.layer?.mask = mask
        let rim = CAShapeLayer()
        rim.frame = bounds
        rim.path = path
        rim.fillColor = NSColor.clear.cgColor
        rim.strokeColor = appearanceTint.color.withAlphaComponent(0.7).cgColor
        rim.lineWidth = 0.65 + 0.5 * glowStrength
        glass.layer?.sublayers?.filter { $0.name == "rim" }.forEach { $0.removeFromSuperlayer() }
        rim.name = "rim"
        glass.layer?.addSublayer(rim)
    }
    override var mouseDownCanMoveWindow: Bool { false }

    override func draw(_ dirtyRect: NSRect) {
        guard let context = NSGraphicsContext.current?.cgContext else { return }
        let path = glyphPath()
        if glowStrength > 0 {
            context.saveGState()
            context.addPath(path)
            context.setFillColor(glowColor.withAlphaComponent(0.8 * glowStrength).cgColor)
            context.setShadow(offset: .zero, blur: 8,
                              color: glowColor.withAlphaComponent(0.95 * glowStrength).cgColor)
            context.fillPath()
            context.restoreGState()
        }
        // A fine dark outside edge remains visible over white content, while
        // the light glass rim remains visible over dark content. This is a
        // contrast treatment, not screen capture or inverse pixel blending.
        context.saveGState()
        context.addPath(path)
        context.setStrokeColor(NSColor.black.withAlphaComponent(0.48).cgColor)
        context.setLineWidth(1.8)
        context.setLineJoin(.round)
        context.setShadow(offset: .zero, blur: 1.5,
                          color: NSColor.black.withAlphaComponent(0.25).cgColor)
        context.strokePath()
        context.restoreGState()
        guard glass == nil else { return }
        if appearanceTint == .red {
            context.saveGState()
            context.addPath(path)
            context.clip()
            if let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                                         colors: [darkRed.cgColor, lightRed.cgColor] as CFArray,
                                         locations: [0, 1]) {
                context.drawLinearGradient(gradient,
                    start: CGPoint(x: bounds.minX, y: bounds.minY),
                    end: CGPoint(x: bounds.maxX, y: bounds.maxY), options: [])
            }
            context.restoreGState()
            return
        }
        context.addPath(path)
        context.setFillColor(appearanceTint.color.cgColor)
        context.setShadow(offset: CGSize(width: 0, height: -1), blur: 3, color: NSColor.black.cgColor)
        context.fillPath()
    }

    override func menu(for event: NSEvent) -> NSMenu? {
        contextMenu?()
    }

    override func mouseDown(with event: NSEvent) {
        if event.clickCount == 2 { onConfigure?(); return }
        guard let window else { return }
        isDragging = true
        onPickUp?()
        refreshUrgencyAnimation()
        glass?.layer?.removeAnimation(forKey: "minuteBounce")
        gradientView.layer?.removeAnimation(forKey: "minuteBounce")
        hovered = true
        NSCursor.closedHand.push()
        defer {
            isDragging = false
            refreshUrgencyAnimation()
            NSCursor.pop()
            let local = convert(window.convertPoint(fromScreen: NSEvent.mouseLocation), from: nil)
            hovered = bounds.contains(local)
        }
        let initialMouse = NSEvent.mouseLocation
        let initialOrigin = window.frame.origin
        while let next = window.nextEvent(matching: [.leftMouseDragged, .leftMouseUp]) {
            let mouse = NSEvent.mouseLocation
            window.setFrameOrigin(NSPoint(x: initialOrigin.x + mouse.x - initialMouse.x,
                                          y: initialOrigin.y + mouse.y - initialMouse.y))
            if next.type == .leftMouseUp {
                isDragging = false
                // Apply any deferred digit-width change once, before choosing
                // the final corner. Timer updates must never move a held panel.
                cachedOutline = nil
                updateGlass()
                needsDisplay = true
                onDrop?(mouse)
                break
            }
        }
    }
}

@MainActor
final class OverlayPanel: NSPanel {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private let model = TimerModel()
    private let stopwatchActivity = StopwatchActivity()
    private var stopwatchActivityEnabled = (UserDefaults.standard.object(forKey: "stopwatchActivityEnabled") as? Bool) ?? true
    private let durationPopover = NSPopover()
    private var panel: NSPanel!
    private let numbers = NumbersView(frame: NSRect(x: 0, y: 0, width: 250, height: 66))
    private var subscription: AnyCancellable?
    private var completionTask: Task<Void, Never>?
    private var completionBorder: ScreenCompletionBorder?
    private var snapTask: Task<Void, Never>?
    private var statusItem: NSStatusItem?
    private var launchReady = false
    private var pendingURLs: [URL] = []
    private let statusMenu = NSMenu()
    private var showingCurrentTime = false
    private lazy var wallClocks = WallClockDisplays(
        openMenu: { [weak self] in self?.openMenu() },
        disable: { [weak self] in self?.setCurrentTime(false) })
    private var corner = Corner(rawValue: UserDefaults.standard.string(forKey: "corner") ?? "") ?? .topRight

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        buildMenu()
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem?.button?.image = TimerSymbol.menuImage
        statusMenu.delegate = self
        statusMenu.autoenablesItems = false
        statusItem?.menu = statusMenu
        statusItem?.button?.toolTip = "hava timer — controls and quit"
        panel = OverlayPanel(contentRect: numbers.frame, styleMask: [.borderless, .nonactivatingPanel],
                        backing: .buffered, defer: false)
        // Above full-screen app toolbars, while remaining below system menus.
        panel.level = .statusBar
        panel.isFloatingPanel = true
        panel.becomesKeyOnlyIfNeeded = true
        panel.worksWhenModal = true
        panel.ignoresMouseEvents = false
        panel.acceptsMouseMovedEvents = true
        panel.hidesOnDeactivate = false
        panel.isReleasedWhenClosed = false
        // macOS passes clicks through completely transparent window pixels,
        // before NSView.hitTest runs. A nearly invisible backing gives the whole
        // tight number rectangle a hit surface, including holes between digits.
        panel.backgroundColor = NSColor.black.withAlphaComponent(0.02)
        panel.isOpaque = false
        panel.hasShadow = false
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.contentView = numbers
        numbers.onPickUp = { [weak self] in
            self?.snapTask?.cancel()
            self?.snapTask = nil
        }
        numbers.onDrop = { [weak self] in self?.snap(at: $0) }
        numbers.onConfigure = { [weak self] in self?.openMenu() }
        numbers.contextMenu = { [weak self] in self?.makeOverlayMenu() ?? NSMenu() }
        numbers.setAccessibilityElement(true)
        numbers.setAccessibilityRole(.staticText)
        subscription = model.$remaining.combineLatest(model.$running).sink { [weak self] state in
            guard let self else { return }
            let (remaining, running) = state
            self.stopwatchActivity.update(running: self.model.mode == .stopwatch && running,
                                          enabled: self.stopwatchActivityEnabled)
            self.numbers.tint = self.model.mode == .stopwatch ? .neutral
                : TimerTint.current(remaining: remaining, duration: self.model.duration)
            let seconds = max(0, Int(self.model.mode == .stopwatch ? floor(remaining) : ceil(remaining)))
            let previousSize = self.panel.frame.size
            let previousText = self.numbers.text
            self.numbers.text = TimerText.format(self.model.mode == .stopwatch ? floor(remaining) : remaining)
            // Move the SVG hand one six-degree tick per elapsed second. Pausing
            // naturally holds it still; Reduce Motion keeps the original icon.
            let elapsed = self.model.mode == .stopwatch ? remaining : max(0, self.model.duration - remaining)
            self.numbers.handAngle = NSWorkspace.shared.accessibilityDisplayShouldReduceMotion
                ? 0 : CGFloat(floor(elapsed).truncatingRemainder(dividingBy: 60) * .pi / 30)
            self.numbers.urgencyGlow = self.model.mode == .countdown && running && remaining > 0 && remaining <= 10
                ? CGFloat(0.15 + 0.85 * pow(sin(.pi * remaining.truncatingRemainder(dividingBy: 1)), 2))
                : nil
            if running && seconds > 0 && seconds % 60 == 0 && self.numbers.text != previousText {
                self.numbers.bounce()
            }
            if self.panel.frame.size != previousSize { self.place(on: self.panel.screen ?? NSScreen.main) }
            self.numbers.setAccessibilityLabel("\(self.model.mode == .stopwatch ? "Elapsed time" : "Time remaining") \(self.numbers.text)")
        }
        model.showOverlay = { [weak self] in
            guard let self else { return }
            self.cancelCompletion()
            self.setCurrentTime(false)
            self.place(on: self.panel.screen ?? NSScreen.main)
            self.panel.orderFrontRegardless()
            self.numbers.bounce()
        }
        model.onComplete = { [weak self] in self?.finishOverlay() }
        model.onReset = { [weak self] in
            self?.cancelCompletion()
            self?.panel.orderOut(nil)
        }
        NotificationCenter.default.addObserver(self, selector: #selector(screensChanged),
            name: NSApplication.didChangeScreenParametersNotification, object: nil)
        NSWorkspace.shared.notificationCenter.addObserver(self, selector: #selector(spaceChanged),
            name: NSWorkspace.activeSpaceDidChangeNotification, object: nil)
        // Launch Services can deliver a Raycast URL before the panel and its
        // callbacks exist. Drain requests only after all presentation is ready.
        launchReady = true
        if UserDefaults.standard.bool(forKey: "showCurrentTime") { setCurrentTime(true) }
        let requests = pendingURLs
        pendingURLs.removeAll()
        if !requests.isEmpty { application(NSApp, open: requests) }
    }

    private func cancelCompletion() {
        completionTask?.cancel()
        completionTask = nil
        completionBorder?.dismiss()
        completionBorder = nil
        numbers.completionGlow = nil
    }

    private func finishOverlay() {
        cancelCompletion()
        completionBorder = ScreenCompletionBorder(screen: panel.screen ?? NSScreen.main)
        completionTask = Task { @MainActor [weak self] in
            guard let self else { return }
            // Three smooth 0.8-second glow pulses; no movement or flashing.
            let steps = 24
            for _ in 0..<3 {
                for frame in 0...steps {
                    guard !Task.isCancelled else { return }
                    let phase = Double(frame) / Double(steps)
                    let intensity = CGFloat(pow(sin(.pi * phase), 2))
                    self.numbers.completionGlow = intensity
                    self.completionBorder?.setGlow(intensity)
                    if frame < steps {
                        do { try await Task.sleep(nanoseconds: 33_333_333) }
                        catch { return }
                    }
                }
            }
            guard !Task.isCancelled else { return }
            self.panel.orderOut(nil)
            self.completionBorder?.dismiss()
            self.completionBorder = nil
            self.numbers.completionGlow = nil
            self.completionTask = nil
        }
    }

    private func makeOverlayMenu() -> NSMenu {
        let menu = NSMenu()
        menu.autoenablesItems = false
        let toggle = NSMenuItem(title: model.running ? "Pause" : "Resume",
            action: #selector(toggleFromMenu), keyEquivalent: "")
        toggle.target = self
        toggle.isEnabled = model.canResume
        menu.addItem(toggle)
        let stop = NSMenuItem(title: "Stop", action: #selector(stopFromMenu), keyEquivalent: "")
        stop.target = self
        stop.isEnabled = model.hasStarted
        menu.addItem(stop)
        if model.mode == .countdown {
            menu.addItem(.separator())
            for (title, seconds) in [("+1 minute", 60), ("+5 minutes", 300)] {
                let item = NSMenuItem(title: title, action: #selector(addTimeFromMenu(_:)), keyEquivalent: "")
                item.target = self
                item.tag = seconds
                item.isEnabled = model.canAddTime(Double(seconds))
                menu.addItem(item)
            }
        }
        return menu
    }

    @objc private func addTimeFromMenu(_ item: NSMenuItem) {
        model.addTime(Double(item.tag))
    }

    @objc private func stopFromMenu() {
        snapTask?.cancel()
        snapTask = nil
        model.stop()
    }

    func menuNeedsUpdate(_ menu: NSMenu) {
        guard menu === statusMenu else { return }
        menu.removeAllItems()
        let state = model.finished ? "Time’s up" : model.running ? "Running" : model.hasStarted ? "Paused" : "Ready"
        let kind = model.mode == .stopwatch ? "stopwatch" : "timer"
        let summaryTitle = showingCurrentTime
            ? "Hava Clock · \(WallClockText.format(Date()))"
            : "hava \(kind) · \(model.display) · \(state)"
        let summary = NSMenuItem(title: summaryTitle, action: nil, keyEquivalent: "")
        summary.isEnabled = false
        menu.addItem(summary)
        menu.addItem(.separator())

        func add(_ title: String, _ action: Selector, enabled: Bool = true) {
            let item = NSMenuItem(title: title, action: action, keyEquivalent: "")
            item.target = self
            item.isEnabled = enabled
            menu.addItem(item)
        }
        if !showingCurrentTime {
            add(model.hasStarted ? "Restart \(kind)" : "Start \(kind)", #selector(startFromMenu),
                enabled: model.mode == .stopwatch || model.validDuration)
            add(model.running ? "Pause \(kind)" : "Resume \(kind)", #selector(toggleFromMenu), enabled: model.canResume)
            add("Reset \(kind)", #selector(resetFromMenu), enabled: model.hasStarted)
            menu.addItem(.separator())
        }

        let durations = NSMenu(title: "Start a new timer")
        durations.autoenablesItems = false
        for minutes in [5, 10, 15, 25, 30, 45, 60] {
            let item = NSMenuItem(title: "\(minutes) minutes", action: #selector(startPreset(_:)), keyEquivalent: "")
            item.tag = minutes
            item.target = self
            durations.addItem(item)
        }
        let custom = NSMenuItem(title: "Custom duration…", action: #selector(showDuration), keyEquivalent: "")
        custom.target = self
        durations.addItem(.separator())
        durations.addItem(custom)
        let presets = NSMenuItem(title: "Start a new timer", action: nil, keyEquivalent: "")
        presets.submenu = durations
        menu.addItem(presets)
        add("Start a new stopwatch", #selector(startStopwatchFromMenu))
        let showTime = NSMenuItem(title: "Hava Clock", action: #selector(toggleCurrentTime), keyEquivalent: "")
        showTime.target = self
        showTime.state = showingCurrentTime ? .on : .off
        menu.addItem(showTime)
        let activity = NSMenuItem(title: "Stopwatch activity", action: nil, keyEquivalent: "")
        let activityMenu = NSMenu(title: "Stopwatch activity")
        let toggleActivity = NSMenuItem(title: "Mouse activity once a minute",
            action: #selector(toggleStopwatchActivity), keyEquivalent: "")
        toggleActivity.target = self
        toggleActivity.state = stopwatchActivityEnabled ? .on : .off
        activityMenu.addItem(toggleActivity)
        let note = NSMenuItem(title: "Only while the stopwatch is running and you’re idle", action: nil, keyEquivalent: "")
        note.isEnabled = false
        activityMenu.addItem(note)
        if !stopwatchActivity.hasPermission {
            activityMenu.addItem(.separator())
            let permission = NSMenuItem(title: "Allow mouse activity…",
                action: #selector(allowStopwatchActivity), keyEquivalent: "")
            permission.target = self
            activityMenu.addItem(permission)
        }
        activity.submenu = activityMenu
        menu.addItem(activity)
        menu.addItem(.separator())
        let quit = NSMenuItem(title: "Quit hava timer", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        quit.target = NSApp
        menu.addItem(quit)
    }

    @objc private func toggleStopwatchActivity() {
        stopwatchActivityEnabled.toggle()
        UserDefaults.standard.set(stopwatchActivityEnabled, forKey: "stopwatchActivityEnabled")
        stopwatchActivity.update(running: model.mode == .stopwatch && model.running, enabled: stopwatchActivityEnabled)
    }

    @objc private func allowStopwatchActivity() { stopwatchActivity.requestPermission() }

    @objc private func toggleCurrentTime() { setCurrentTime(!showingCurrentTime) }

    private func setCurrentTime(_ enabled: Bool) {
        guard enabled != showingCurrentTime else { return }
        if enabled {
            // Mode switches replace the active timer/stopwatch, as starting a
            // new timer does. Clock mode does not run countdown effects.
            model.stop()
            cancelCompletion()
            snapTask?.cancel()
            snapTask = nil
            panel.orderOut(nil)
        }
        showingCurrentTime = enabled
        UserDefaults.standard.set(enabled, forKey: "showCurrentTime")
        if enabled { wallClocks.show() } else { wallClocks.hide() }
    }

    @objc private func startFromMenu() {
        if model.mode == .stopwatch { model.startStopwatch() } else { model.start() }
    }
    @objc private func startStopwatchFromMenu() { model.startStopwatch() }
    @objc private func toggleFromMenu() {
        if model.running { model.pause() } else { model.resume() }
    }
    @objc private func resetFromMenu() { model.reset() }
    @objc private func startPreset(_ item: NSMenuItem) {
        model.minutes = Double(item.tag)
        model.start()
    }

    private func buildMenu() {
        let menu = NSMenu()
        let item = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Custom timer…", action: #selector(showDuration), keyEquivalent: "0").target = self
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Quit hava timer", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        menu.addItem(item)
        let edit = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        edit.submenu = editMenu
        menu.addItem(edit)
        NSApp.mainMenu = menu
    }

    @objc private func showDuration() {
        guard let button = statusItem?.button else { return }
        let editor = DurationEditor()
        editor.minutes = model.minutes
        editor.onStart = { [weak self] minutes in
            guard let self else { return }
            self.model.minutes = minutes
            self.model.start()
            self.durationPopover.performClose(nil)
        }
        editor.onCancel = { [weak self] in self?.durationPopover.performClose(nil) }
        durationPopover.contentViewController = editor
        durationPopover.behavior = .transient
        durationPopover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
    }

    private func openMenu() {
        durationPopover.performClose(nil)
        statusItem?.button?.performClick(nil)
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        // A URL launch must not enter a blocking menu-tracking loop before its
        // start command is delivered. Controls open explicitly via /menu.
        return false
    }

    private func place(on screen: NSScreen?, animated: Bool = false) {
        guard !numbers.isDragging else { return }
        snapTask?.cancel()
        snapTask = nil
        guard let screen = screen ?? NSScreen.screens.first else { return }
        let bounds = screen.visibleFrame.insetBy(dx: 2, dy: 2)
        let left = corner == .topLeft || corner == .bottomLeft
        let top = corner == .topLeft || corner == .topRight
        let origin = NSPoint(x: left ? bounds.minX : bounds.maxX - panel.frame.width,
                             y: top ? bounds.maxY - panel.frame.height : bounds.minY)
        if animated && !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion {
            let start = panel.frame.origin
            snapTask = Task { @MainActor [weak self] in
                guard let self else { return }
                for step in 1...20 {
                    do { try await Task.sleep(nanoseconds: 16_000_000) }
                    catch { return }
                    guard !Task.isCancelled, !self.numbers.isDragging else { return }
                    let progress = Double(step) / 20
                    let eased = CGFloat(1 - pow(1 - progress, 3))
                    self.panel.setFrameOrigin(NSPoint(x: start.x + (origin.x - start.x) * eased,
                                                      y: start.y + (origin.y - start.y) * eased))
                }
                self.snapTask = nil
            }
        } else {
            panel.setFrameOrigin(origin)
        }
    }

    private func snap(at mouse: NSPoint) {
        guard let screen = NSScreen.screens.first(where: { $0.frame.contains(mouse) }) ?? panel.screen ?? NSScreen.main else { return }
        let bounds = screen.visibleFrame.insetBy(dx: 2, dy: 2)
        let candidates: [(Corner, NSPoint)] = [
            (.topRight, NSPoint(x: bounds.maxX - panel.frame.width / 2, y: bounds.maxY - panel.frame.height / 2)),
            (.bottomRight, NSPoint(x: bounds.maxX - panel.frame.width / 2, y: bounds.minY + panel.frame.height / 2)),
            (.bottomLeft, NSPoint(x: bounds.minX + panel.frame.width / 2, y: bounds.minY + panel.frame.height / 2)),
            (.topLeft, NSPoint(x: bounds.minX + panel.frame.width / 2, y: bounds.maxY - panel.frame.height / 2))
        ]
        let center = NSPoint(x: panel.frame.midX, y: panel.frame.midY)
        corner = candidates.min {
            hypot($0.1.x - center.x, $0.1.y - center.y) < hypot($1.1.x - center.x, $1.1.y - center.y)
        }!.0
        UserDefaults.standard.set(corner.rawValue, forKey: "corner")
        place(on: screen, animated: true)
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        guard launchReady else {
            pendingURLs.append(contentsOf: urls)
            return
        }
        for url in urls {
            if url.scheme == "hava-timer", url.host == "stopwatch" {
                model.startStopwatch()
                continue
            }
            if url.scheme == "hava-timer", url.host == "clock" {
                setCurrentTime(true)
                continue
            }
            if url.scheme == "hava-timer", url.host == "quit" || url.host == "stop" {
                stopFromMenu()
                NSApp.terminate(nil)
                return
            }
            if url.scheme == "hava-timer", url.host == "menu" {
                openMenu()
                continue
            }
            guard url.scheme == "hava-timer", url.host == "start",
                  let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
                  let value = components.queryItems?.first(where: { $0.name == "minutes" })?.value,
                  let minutes = Double(value), minutes.isFinite, (1...1440).contains(minutes) else { continue }
            model.minutes = minutes
            model.start()
        }
    }

    @objc private func spaceChanged() {
        if showingCurrentTime { wallClocks.bringForward() }
        guard panel.isVisible else { return }
        // Reassert ordering on entry to another app's full-screen Space.
        panel.orderFrontRegardless()
        completionBorder?.bringForward()
    }

    func applicationWillTerminate(_ notification: Notification) {
        stopwatchActivity.stop()
        completionTask?.cancel()
        snapTask?.cancel()
        completionBorder?.dismiss()
        wallClocks.hide()
        NotificationCenter.default.removeObserver(self)
        NSWorkspace.shared.notificationCenter.removeObserver(self)
    }

    @objc private func screensChanged() {
        if showingCurrentTime { wallClocks.reconcileScreens() }
        place(on: panel.screen ?? NSScreen.main)
        completionBorder?.move(to: panel.screen ?? NSScreen.main)
    }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = AppDelegate()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
