import Markdown

struct MarkdownRenderer {
    func render(markdown: String) -> String {
        let document = Document(parsing: markdown)
        return HTMLFormatter.format(document)
    }
}
