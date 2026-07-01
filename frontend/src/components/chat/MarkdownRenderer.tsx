interface Props {
  content: string;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderInline(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

function renderBlock(block: string): string {
  const trimmed = block.trim();
  if (!trimmed) return "";

  if (/^###\s/.test(trimmed)) {
    return `<h3>${renderInline(trimmed.slice(3))}</h3>`;
  }
  if (/^##\s/.test(trimmed)) {
    return `<h2>${renderInline(trimmed.slice(2))}</h2>`;
  }
  if (/^#\s/.test(trimmed)) {
    return `<h1>${renderInline(trimmed.slice(1))}</h1>`;
  }

  const lines = trimmed.split("\n");
  const firstLine = lines[0].trim();

  if (/^[-*]\s/.test(firstLine)) {
    const items = lines
      .map(l => l.replace(/^[-*]\s/, "").trim())
      .filter(Boolean)
      .map(l => `<li>${renderInline(l)}</li>`)
      .join("");
    return `<ul>${items}</ul>`;
  }

  if (/^\d+\.\s/.test(firstLine)) {
    const items = lines
      .map(l => l.replace(/^\d+\.\s/, "").trim())
      .filter(Boolean)
      .map(l => `<li>${renderInline(l)}</li>`)
      .join("");
    return `<ol>${items}</ol>`;
  }

  return `<p>${renderInline(trimmed)}</p>`;
}

export default function MarkdownRenderer({ content }: Props) {
  const blocks = content.split(/\n\n+/);
  const html = blocks.map(renderBlock).filter(Boolean).join("");
  return (
    <div className="prose prose-sm max-w-none">
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
