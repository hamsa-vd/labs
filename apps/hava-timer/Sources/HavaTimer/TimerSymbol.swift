import AppKit

// Use the supplied SVG's actual vector outline for both the menu bar template
// and the floating glass mask. No font substitution or raster scaling.
enum TimerSymbol {
    private static let parts: [CGPath] = {
        guard let url = Bundle.main.url(forResource: "timer", withExtension: "svg")
                ?? Bundle.module.url(forResource: "timer", withExtension: "svg"),
              let svg = try? String(contentsOf: url, encoding: .utf8),
              let attribute = try? NSRegularExpression(pattern: "\\sd=\"([^\"]+)\"") else { return [] }
        return attribute.matches(in: svg, range: NSRange(svg.startIndex..., in: svg))
            .compactMap { Range($0.range(at: 1), in: svg).map { String(svg[$0]) } }
            .map { parse($0) }
    }()

    private static let outline: CGPath = {
        let combined = CGMutablePath()
        parts.forEach { combined.addPath($0) }
        return combined.normalized(using: .winding)
    }()

    private static func parse(_ data: String) -> CGPath {
        let empty = CGMutablePath()
        guard let tokenizer = try? NSRegularExpression(pattern: "[A-Za-z]|[-+]?(?:[0-9]*\\.)?[0-9]+(?:[eE][-+]?[0-9]+)?") else { return empty }
        let tokens = tokenizer.matches(in: data, range: NSRange(data.startIndex..., in: data)).compactMap {
            Range($0.range, in: data).map { String(data[$0]) }
        }
        let path = CGMutablePath()
        var index = 0
        var command = ""
        var current = CGPoint.zero
        var start = CGPoint.zero
        func number() -> CGFloat? {
            guard index < tokens.count, let value = Double(tokens[index]), value.isFinite else { return nil }
            index += 1
            return CGFloat(value)
        }
        while index < tokens.count {
            if tokens[index].first?.isLetter == true {
                command = tokens[index]
                index += 1
            }
            switch command {
            case "M", "L":
                guard let x = number(), let y = number() else { return empty }
                current = CGPoint(x: x, y: y)
                if command == "M" {
                    path.move(to: current)
                    start = current
                    command = "L"
                } else { path.addLine(to: current) }
            case "H":
                guard let x = number() else { return empty }
                current.x = x
                path.addLine(to: current)
            case "V":
                guard let y = number() else { return empty }
                current.y = y
                path.addLine(to: current)
            case "C":
                guard let x1 = number(), let y1 = number(), let x2 = number(), let y2 = number(),
                      let x = number(), let y = number() else { return empty }
                current = CGPoint(x: x, y: y)
                path.addCurve(to: current, control1: CGPoint(x: x1, y: y1), control2: CGPoint(x: x2, y: y2))
            case "Z":
                path.closeSubpath()
                current = start
                command = ""
            default:
                // The checked-in SVG uses absolute M/L/H/V/C/Z commands.
                // Reject unsupported data rather than silently drawing it wrong.
                return empty
            }
        }
        return path.normalized(using: .winding)
    }

    static var aspectRatio: CGFloat {
        let box = outline.boundingBoxOfPath
        return box.height > 0 ? box.width / box.height : 0.62
    }

    static func path(in rect: NSRect, handAngle: CGFloat = 0) -> CGPath {
        let box = outline.boundingBoxOfPath
        guard !outline.isEmpty, box.width > 0, box.height > 0 else { return CGMutablePath() }
        let scale = min(rect.width / box.width, rect.height / box.height)
        // SVG has its origin at the top left; AppKit drawing has it at bottom left.
        var transform = CGAffineTransform(a: scale, b: 0, c: 0, d: -scale,
            tx: rect.midX - box.midX * scale, ty: rect.midY + box.midY * scale)
        let moving = CGMutablePath()
        for (index, part) in parts.enumerated() {
            if index == 0 && parts.count == 4 && handAngle != 0 {
                // The first path in the supplied clock SVG is its hand;
                // rotate it about the hand's hub in SVG coordinates.
                let pivot = CGPoint(x: 56, y: 59)
                let rotation = CGAffineTransform(translationX: pivot.x, y: pivot.y)
                    .rotated(by: handAngle).translatedBy(x: -pivot.x, y: -pivot.y)
                moving.addPath(part, transform: rotation)
            } else { moving.addPath(part) }
        }
        return moving.copy(using: &transform)!.normalized(using: .winding)
    }

    static var menuImage: NSImage {
        let image = NSImage(size: NSSize(width: 18, height: 18), flipped: false) { rect in
            guard let context = NSGraphicsContext.current?.cgContext else { return false }
            context.addPath(path(in: rect.insetBy(dx: 1, dy: 1)))
            context.setFillColor(NSColor.black.cgColor)
            context.fillPath()
            return true
        }
        image.isTemplate = true
        image.accessibilityDescription = "hava timer"
        return image
    }
}
