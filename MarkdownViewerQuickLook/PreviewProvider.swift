import Foundation
import QuickLookUI
import UniformTypeIdentifiers

final class PreviewProvider: QLPreviewProvider {
    func providePreview(for request: QLFilePreviewRequest) async throws -> QLPreviewReply {
        let fileURL = request.fileURL

        let markdown = try String(contentsOf: fileURL)
        let renderer = MarkdownRenderer()
        let body = renderer.render(markdown: markdown)
        let html = self.wrappedHTML(body: body)

        let reply = QLPreviewReply(dataOfContentType: .html, contentSize: .zero) { reply in
            reply.title = fileURL.lastPathComponent
            reply.attachments = self.loadAttachments()
            return Data(html.utf8)
        }

        return reply
    }

    private func wrappedHTML(body: String) -> String {
        return """
        <!doctype html>
        <html>
          <head>
            <meta charset=\"utf-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
            <link rel=\"stylesheet\" href=\"cid:markdown.css\">
            <script src=\"cid:mermaid.min.js\" defer></script>
            <script src=\"cid:markdown.js\" defer></script>
          </head>
          <body>
            <article class=\"markdown-body\">
              \(body)
            </article>
          </body>
        </html>
        """
    }

    private func loadAttachments() -> [String: QLPreviewReplyAttachment] {
        var attachments: [String: QLPreviewReplyAttachment] = [:]
        let bundle = Bundle(for: PreviewProvider.self)

        if let css = loadResourceData(named: "markdown", fileExtension: "css", bundle: bundle) {
            attachments["markdown.css"] = QLPreviewReplyAttachment(data: css, contentType: cssContentType())
        }

        if let js = loadResourceData(named: "markdown", fileExtension: "js", bundle: bundle) {
            attachments["markdown.js"] = QLPreviewReplyAttachment(data: js, contentType: .javaScript)
        }

        if let mermaid = loadResourceData(named: "mermaid.min", fileExtension: "js", bundle: bundle) {
            attachments["mermaid.min.js"] = QLPreviewReplyAttachment(data: mermaid, contentType: .javaScript)
        }

        return attachments
    }

    private func loadResourceData(named name: String, fileExtension: String, bundle: Bundle) -> Data? {
        guard let url = bundle.url(forResource: name, withExtension: fileExtension) else {
            return nil
        }
        return try? Data(contentsOf: url)
    }

    private func cssContentType() -> UTType {
        if #available(macOS 15.0, *) {
            return .css
        }
        return UTType(filenameExtension: "css") ?? .plainText
    }
}
