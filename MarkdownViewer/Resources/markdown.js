const resolveMermaidTheme = () => {
  const html = document.documentElement;
  if (html.dataset.theme === "dark") return "dark";
  if (html.dataset.theme === "light") return "default";
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "default";
};

document.addEventListener("DOMContentLoaded", () => {
  const mermaidNodes = [];

  document.querySelectorAll("pre").forEach((block) => {
    const code = block.querySelector("code");
    if (!code) return;

    const classList = Array.from(code.classList);
    const langClass = classList.find((c) => c.startsWith("language-"));
    const language = langClass ? langClass.replace("language-", "") : null;
    const isMermaid = language === "mermaid" || classList.includes("mermaid");

    if (isMermaid) {
      const container = document.createElement("div");
      container.className = "mermaid";
      container.textContent = code.textContent;
      block.replaceWith(container);
      mermaidNodes.push(container);
      return;
    }

    if (window.hljs && typeof window.hljs.highlightElement === "function") {
      window.hljs.highlightElement(code);
    }

    if (langClass) {
      const header = document.createElement("div");
      header.className = "code-header";
      header.innerText = language;
      block.appendChild(header);
    }

    const button = document.createElement("button");
    button.innerText = "Copy";
    button.className = "copy-btn";

    button.addEventListener("click", async () => {
      const text = code.innerText;

      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          const textarea = document.createElement("textarea");
          textarea.value = text;
          textarea.style.position = "fixed";
          textarea.style.top = "-1000px";
          textarea.style.left = "-1000px";
          document.body.appendChild(textarea);
          textarea.focus();
          textarea.select();
          document.execCommand("copy");
          document.body.removeChild(textarea);
        }

        button.innerText = "Copied!";
        setTimeout(() => (button.innerText = "Copy"), 1500);
      } catch (e) {
        button.innerText = "Failed";
        setTimeout(() => (button.innerText = "Copy"), 1500);
      }
    });

    block.appendChild(button);
  });

  if (mermaidNodes.length && window.mermaid) {
    try {
      window.mermaid.initialize({
        startOnLoad: false,
        theme: resolveMermaidTheme(),
      });
      window.mermaid.run({ nodes: mermaidNodes });
    } catch (e) {
      console.warn("Mermaid render failed", e);
    }
  }
});
