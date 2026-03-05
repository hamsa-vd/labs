import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @State private var html: String = ""
    @State private var renderedBody: String = ""
    @State private var isImporterPresented = false
    @State private var isDropTargeted = false
    @State private var currentFileName: String?
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var fontScale: Double = 1.0
    @State private var panelOpacity: Double = 0.75
    @State private var windowOpacity: Double = 1.0
    @State private var appearanceMode: AppearanceMode = .system
    @State private var isSettingsPresented = false

    @Environment(\.colorScheme) private var systemColorScheme

    private let renderer = MarkdownRenderer()

    var body: some View {
        VStack(spacing: 0) {
            Group {
                if html.isEmpty {
                    ZStack {
                        appBackgroundColor
                            .ignoresSafeArea()

                        VStack(spacing: 12) {
                            Text("No Markdown file loaded")
                                .font(.title2)
                            Text("Choose a .md or .markdown file to preview.")
                                .foregroundStyle(.secondary)
                        }
                        .padding(28)
                        .background(
                            RoundedRectangle(cornerRadius: 16, style: .continuous)
                                .fill(panelBackgroundColor)
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 16, style: .continuous)
                                .strokeBorder(panelBorderColor, lineWidth: 1)
                        )
                    }
                } else {
                    WebView(html: html)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(appBackgroundColor)
        .frame(minWidth: 640, minHeight: 480)
        .overlay {
            if isDropTargeted {
                RoundedRectangle(cornerRadius: 12)
                    .strokeBorder(
                        Color.accentColor,
                        style: StrokeStyle(lineWidth: 2, dash: [6])
                    )
                    .padding(12)
            }
        }
        .fileImporter(
            isPresented: $isImporterPresented,
            allowedContentTypes: allowedContentTypes,
            allowsMultipleSelection: false,
            onCompletion: handleImport(result:)
        )
        .onOpenURL { url in
            handleOpenURL(url)
        }
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button {
                    isImporterPresented = true
                } label: {
                    Label("Open File", systemImage: "folder")
                }

                Button {
                    zoomOut()
                } label: {
                    Image(systemName: "minus.magnifyingglass")
                }
                .help("Zoom Out")

                Text("\(Int(fontScale * 100))%")
                    .monospacedDigit()
                    .frame(minWidth: 44)

                Button {
                    zoomIn()
                } label: {
                    Image(systemName: "plus.magnifyingglass")
                }
                .help("Zoom In")

                Menu {
                    Picker("Appearance", selection: $appearanceMode) {
                        ForEach(AppearanceMode.allCases) { mode in
                            Text(mode.label).tag(mode)
                        }
                    }
                } label: {
                    Label("Appearance", systemImage: "circle.lefthalf.filled")
                }

                Button {
                    isSettingsPresented.toggle()
                } label: {
                    Image(systemName: "slider.horizontal.3")
                }
                .help("Display Settings")
            }
        }
        .onDrop(of: [UTType.fileURL], isTargeted: $isDropTargeted, perform: handleDrop(providers:))
        .onAppear {
            updateWindowTitle()
            applyAppearance()
            applyWindowOpacity()
        }
        .onChange(of: currentFileName) { _ in
            updateWindowTitle()
        }
        .onChange(of: fontScale) { _ in
            updateHTML()
        }
        .onChange(of: panelOpacity) { _ in
            updateHTML()
        }
        .onChange(of: appearanceMode) { _ in
            applyAppearance()
            updateHTML()
        }
        .onChange(of: windowOpacity) { _ in
            applyWindowOpacity()
        }
        .popover(isPresented: $isSettingsPresented, arrowEdge: .bottom) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Display").font(.headline)

                HStack {
                    Text("Panel Opacity")
                        .frame(width: 110, alignment: .leading)
                    Slider(value: $panelOpacity, in: 0.3...1.0, step: 0.05)
                    Text("\(Int(panelOpacity * 100))%")
                        .monospacedDigit()
                        .frame(width: 44, alignment: .trailing)
                }

                HStack {
                    Text("Window Opacity")
                        .frame(width: 110, alignment: .leading)
                    Slider(value: $windowOpacity, in: 0.6...1.0, step: 0.05)
                    Text("\(Int(windowOpacity * 100))%")
                        .monospacedDigit()
                        .frame(width: 44, alignment: .trailing)
                }
            }
            .padding(16)
            .frame(width: 260)
        }
        .alert("Unable to Open File", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
    }

    private var allowedContentTypes: [UTType] {
        ["md", "markdown"].compactMap { UTType(filenameExtension: $0) }
    }

    private func handleImport(result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            loadMarkdown(from: url)
        case .failure(let error):
            presentError(error)
        }
    }

    private func handleOpenURL(_ url: URL) {
        guard url.isFileURL else { return }
        guard isSupportedMarkdownFile(url) else {
            presentErrorMessage("Only .md and .markdown files are supported.")
            return
        }
        loadMarkdown(from: url)
    }

    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first(where: {
            $0.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier)
        }) else {
            return false
        }

        provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
            DispatchQueue.main.async {
                if let error = error {
                    presentError(error)
                    return
                }

                let url = extractURL(from: item)
                guard let url else {
                    presentErrorMessage("Unable to read the dropped file.")
                    return
                }
                guard isSupportedMarkdownFile(url) else {
                    presentErrorMessage("Only .md and .markdown files are supported.")
                    return
                }

                loadMarkdown(from: url)
            }
        }

        return true
    }

    private func extractURL(from item: NSSecureCoding?) -> URL? {
        if let url = item as? URL {
            return url
        }
        if let data = item as? Data {
            return URL(dataRepresentation: data, relativeTo: nil)
        }
        return nil
    }

    private func isSupportedMarkdownFile(_ url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        return ext == "md" || ext == "markdown"
    }

    private func loadMarkdown(from url: URL) {
        let didAccess = url.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                url.stopAccessingSecurityScopedResource()
            }
        }

        do {
            let contents = try String(contentsOf: url)
            let body = renderer.render(markdown: contents)
            renderedBody = body
            updateHTML()
            currentFileName = url.lastPathComponent
        } catch {
            presentError(error)
        }
    }

    private func presentError(_ error: Error) {
        errorMessage = error.localizedDescription
        showError = true
    }

    private func presentErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }

    private func zoomIn() {
        fontScale = min(fontScale + 0.1, 1.8)
    }

    private func zoomOut() {
        fontScale = max(fontScale - 0.1, 0.6)
    }

    private func updateHTML() {
        guard !renderedBody.isEmpty else {
            html = ""
            return
        }
        html = wrappedHTML(body: renderedBody)
    }

    private func wrappedHTML(body: String) -> String {
        let themeAttribute = appearanceMode.htmlAttribute.map { " data-theme=\\\"\($0)\\\"" } ?? ""
        let fontScaleValue = cssNumber(fontScale)
        let opacityValue = cssNumber(panelOpacity)
        return """
        <!doctype html>
        <html\(themeAttribute) style="--font-scale: \(fontScaleValue); --panel-opacity: \(opacityValue);">
          <head>
            <meta charset=\"utf-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
            <link rel="stylesheet" href="markdown.css">
            <script src="mermaid.min.js" defer></script>
            <script src="markdown.js" defer></script>
          </head>
          <body>
            <article class="markdown-body">
              \(body)
            </article>
          </body>
        </html>
        """
    }

    private func updateWindowTitle() {
        let title = currentFileName ?? "MarkdownViewer"
        if let window = NSApp.keyWindow ?? NSApp.mainWindow {
            window.title = title
        }
    }

    private func applyAppearance() {
        switch appearanceMode {
        case .system:
            NSApp.appearance = nil
        case .light:
            NSApp.appearance = NSAppearance(named: .aqua)
        case .dark:
            NSApp.appearance = NSAppearance(named: .darkAqua)
        }
    }

    private func applyWindowOpacity() {
        let window = NSApp.keyWindow ?? NSApp.mainWindow ?? NSApp.windows.first
        guard let window else { return }
        window.isOpaque = false
        window.backgroundColor = .clear
        window.alphaValue = windowOpacity
    }

    private var effectiveColorScheme: ColorScheme {
        switch appearanceMode {
        case .system:
            return systemColorScheme
        case .light:
            return .light
        case .dark:
            return .dark
        }
    }

    private var appBackgroundColor: Color {
        switch effectiveColorScheme {
        case .light:
            return Color(.sRGB, red: 245.0 / 255.0, green: 246.0 / 255.0, blue: 248.0 / 255.0, opacity: 1.0)
        case .dark:
            return Color(.sRGB, red: 9.0 / 255.0, green: 10.0 / 255.0, blue: 10.0 / 255.0, opacity: 1.0)
        @unknown default:
            return Color(.sRGB, red: 9.0 / 255.0, green: 10.0 / 255.0, blue: 10.0 / 255.0, opacity: 1.0)
        }
    }

    private var panelBackgroundColor: Color {
        switch effectiveColorScheme {
        case .light:
            return Color(.sRGB, red: 1.0, green: 1.0, blue: 1.0, opacity: panelOpacity)
        case .dark:
            return Color(.sRGB, red: 18.0 / 255.0, green: 20.0 / 255.0, blue: 24.0 / 255.0, opacity: panelOpacity)
        @unknown default:
            return Color(.sRGB, red: 18.0 / 255.0, green: 20.0 / 255.0, blue: 24.0 / 255.0, opacity: panelOpacity)
        }
    }

    private var panelBorderColor: Color {
        switch effectiveColorScheme {
        case .light:
            return Color.black.opacity(0.08)
        case .dark:
            return Color.white.opacity(0.08)
        @unknown default:
            return Color.white.opacity(0.08)
        }
    }

    private func cssNumber(_ value: Double) -> String {
        String(format: "%.2f", locale: Locale(identifier: "en_US_POSIX"), value)
    }

    private enum AppearanceMode: String, CaseIterable, Identifiable {
        case system
        case light
        case dark

        var id: String { rawValue }

        var label: String {
            switch self {
            case .system:
                return "System"
            case .light:
                return "Light"
            case .dark:
                return "Dark"
            }
        }

        var htmlAttribute: String? {
            switch self {
            case .system:
                return nil
            case .light:
                return "light"
            case .dark:
                return "dark"
            }
        }
    }
}

#Preview {
    ContentView()
}
