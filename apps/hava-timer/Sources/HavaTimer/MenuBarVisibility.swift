import AppKit

enum MenuBarVisibility {
    struct Window {
        let frame: CGRect
        let level: Int
        let alpha: Double
        let owner: String?
    }

    static func isMenuBar(_ window: Window, on screen: CGRect) -> Bool {
        guard window.level == Int(CGWindowLevelForKey(.mainMenuWindow)), window.alpha > 0.01,
              window.frame.height >= 10, window.frame.height <= 96 else { return false }
        if let owner = window.owner {
            let name = owner.lowercased().replacingOccurrences(of: " ", with: "")
            guard ["windowserver", "systemuiserver", "controlcenter"].contains(name) else { return false }
        }
        let visible = window.frame.intersection(screen)
        // Partially revealed auto-hidden menu bars count once they are usable.
        // Clock overlays and menu popups cannot match this level/width/height.
        return !visible.isNull && visible.width >= screen.width * 0.8 && visible.height >= 8
            && visible.minY >= screen.maxY - 96 && visible.maxY >= screen.maxY - 48
    }

    static func visible(on screen: CGRect, windows: [Window], fallback: Bool) -> Bool {
        if windows.contains(where: { isMenuBar($0, on: screen) }) { return true }
        // When there is a menu-bar window on another monitor, its absence on
        // this monitor is meaningful; never borrow that other monitor's state.
        if windows.contains(where: { $0.level == Int(CGWindowLevelForKey(.mainMenuWindow)) }) { return false }
        return fallback
    }

    @MainActor
    static func snapshot() -> (windows: [Window], fallback: Bool) {
        // Only inspect system window geometry, not images or other apps' text.
        // This requires no Accessibility or Screen Recording permission prompt.
        let options = NSApp.currentSystemPresentationOptions
        let fallback = NSMenu.menuBarVisible()
            && !options.contains(.hideMenuBar) && !options.contains(.autoHideMenuBar)
        guard let primary = NSScreen.screens.first,
              let info = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements],
                                                     kCGNullWindowID) as? [[String: Any]] else {
            return ([], fallback)
        }
        let windows = info.compactMap { entry -> Window? in
            guard let level = entry[kCGWindowLayer as String] as? NSNumber,
                  level.intValue == Int(CGWindowLevelForKey(.mainMenuWindow)),
                  let bounds = entry[kCGWindowBounds as String] as? [String: Any],
                  let cgFrame = CGRect(dictionaryRepresentation: bounds as CFDictionary) else { return nil }
            // Window Server bounds use a top-left origin relative to the
            // primary display. AppKit uses a bottom-left global coordinate space.
            let frame = CGRect(x: cgFrame.minX, y: primary.frame.maxY - cgFrame.maxY,
                               width: cgFrame.width, height: cgFrame.height)
            return Window(frame: frame, level: level.intValue,
                alpha: (entry[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 1,
                owner: entry[kCGWindowOwnerName as String] as? String)
        }
        return (windows, fallback)
    }
}
