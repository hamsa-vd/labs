"""Resume parser — extract plain text from PDF, LaTeX (.tex), or plain text."""

from __future__ import annotations

import re
from pathlib import Path


def parse(source: str | Path) -> str:
    """Return plain text from a resume.

    Args:
        source: file path (PDF or .tex) OR raw text string.

    Returns:
        Plain text with whitespace normalised.
    """
    raw = str(source)

    # Only attempt file path resolution if the string looks like a path
    # (no newlines, plausible length for a filesystem path)
    if "\n" not in raw and len(raw) < 512:
        p = Path(raw)
        try:
            if p.exists():
                if p.suffix.lower() == ".pdf":
                    return _parse_pdf(p)
                if p.suffix.lower() == ".tex":
                    return _parse_latex(p.read_text(encoding="utf-8"))
                return _normalise(p.read_text(encoding="utf-8"))
        except OSError:
            pass  # not a valid path — fall through to raw string handling

    if raw.strip().startswith(r"\documentclass") or r"\begin{document}" in raw:
        return _parse_latex(raw)
    return _normalise(raw)


def _parse_pdf(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        return _normalise("\n".join(pages))
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF parsing. Install with: pip install pymupdf"
        ) from exc


def _parse_latex(latex: str) -> str:
    """Strip LaTeX commands and return readable prose."""
    text = latex

    # Remove preamble (everything before \begin{document})
    text = re.sub(r"(?s)^.*?\\begin\{document\}", "", text)
    # Remove \end{document}
    text = re.sub(r"\\end\{document\}.*$", "", text, flags=re.DOTALL)

    # Expand common display macros to their text content
    text = re.sub(r"\\textbf\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\textit\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\underline\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\href\{[^}]+\}\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\url\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\section\*?\{([^}]+)\}", r"\n\1\n", text)
    text = re.sub(r"\\subsection\*?\{([^}]+)\}", r"\n\1\n", text)
    text = re.sub(r"\\resumeHeader\{([^{}]+)\}\{([^{}]+)\}", r"\1 | \2", text)

    # Convert \item to bullet markers BEFORE stripping other commands
    text = re.sub(r"\\item\b", "\n- ", text)
    text = re.sub(r"\\end\{[^}]+\}", "", text)

    # Remove remaining LaTeX commands (backslash + word + optional braces)
    text = re.sub(r"\\[a-zA-Z]+\*?(\{[^}]*\})*", " ", text)

    # Clean LaTeX size/spacing artifacts (e.g. .17ex from \vspace{.17ex}) 
    text = re.sub(r"\.\d+ex\b", " ", text)
    text = re.sub(r"\b\d+pt\b", " ", text)
    text = text.replace("``", '"').replace("''", '"')
    text = text.replace("\\$", "$").replace("\\%", "%").replace("\\&", "&")

    # Remove leftover braces, brackets, comments
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"%.*$", "", text, flags=re.MULTILINE)

    return _normalise(text)


def _normalise(text: str) -> str:
    """Collapse whitespace and strip leading/trailing blanks."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
