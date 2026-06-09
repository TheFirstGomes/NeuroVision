"""
Converts ENTREGA_FIAP_GS.md to a styled PDF for FIAP Global Solution submission.
Run from the neurovision/ root:  python tools/generate_pdf.py
"""

import re
import base64
import mimetypes
import markdown
from xhtml2pdf import pisa
from pathlib import Path

ROOT = Path(__file__).parent.parent
MD_FILE = ROOT / "ENTREGA_FIAP_GS.md"
OUT_FILE = ROOT / "ENTREGA_FIAP_GS.pdf"

CSS_STYLE = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
}

body {
    font-family: Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #1a1a1a;
}

h1 {
    font-size: 17pt;
    font-weight: bold;
    color: #cc0000;
    border-bottom: 2px solid #cc0000;
    padding-bottom: 5px;
    margin-top: 26px;
    margin-bottom: 10px;
}

h2 {
    font-size: 13pt;
    font-weight: bold;
    color: #222;
    margin-top: 20px;
    margin-bottom: 8px;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    color: #444;
    margin-top: 16px;
    margin-bottom: 5px;
}

h4 {
    font-size: 10.5pt;
    font-weight: bold;
    color: #555;
    margin-top: 12px;
    margin-bottom: 4px;
}

p { margin: 5px 0 9px 0; }

strong { color: #111; }

pre {
    background: #f4f4f4;
    color: #222;
    padding: 10px 14px;
    font-size: 8.5pt;
    line-height: 1.4;
    white-space: pre-wrap;
    margin: 10px 0;
    border-left: 3px solid #cc0000;
}

code {
    background: #f0f0f0;
    color: #c7254e;
    padding: 1px 3px;
    font-size: 9pt;
    font-family: Courier, monospace;
}

pre code {
    background: none;
    color: inherit;
    padding: 0;
    font-size: 8.5pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9.5pt;
}

th {
    background: #cc0000;
    color: white;
    padding: 6px 9px;
    text-align: left;
    font-weight: bold;
}

td {
    padding: 5px 9px;
    border-bottom: 1px solid #ddd;
}

img {
    max-width: 100%;
    display: block;
    margin: 12px auto;
}

blockquote {
    border-left: 4px solid #cc0000;
    margin: 10px 0;
    padding: 7px 14px;
    background: #fff5f5;
    color: #333;
    font-style: italic;
}

hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 18px 0;
}

ul, ol {
    padding-left: 20px;
    margin: 5px 0 9px 0;
}

li { margin: 2px 0; }
"""


def img_to_data_uri(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        mime = "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def embed_images(text: str, base_dir: Path) -> str:
    """Replace relative image paths with base64 data URIs."""
    def replace(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith("http") or src.startswith("data:"):
            return m.group(0)
        img_path = (base_dir / src).resolve()
        if img_path.exists():
            return f'![{alt}]({img_to_data_uri(img_path)})'
        print(f"  [aviso] imagem não encontrada: {img_path}")
        return m.group(0)
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace, text)


def convert(md_path: Path, out_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    text = embed_images(text, md_path.parent)

    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"toc": {"title": "Sumário"}},
    )
    body_html = md.convert(text)

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>NeuroVision — FIAP Global Solution 2025</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
{body_html}
</body>
</html>"""

    with open(out_path, "wb") as fp:
        result = pisa.CreatePDF(
            full_html.encode("utf-8"),
            dest=fp,
            encoding="utf-8",
        )

    if result.err:
        print(f"Erros ao gerar PDF: {result.err}")
    else:
        size_kb = out_path.stat().st_size // 1024
        print(f"PDF gerado: {out_path}  ({size_kb} KB)")


if __name__ == "__main__":
    convert(MD_FILE, OUT_FILE)
