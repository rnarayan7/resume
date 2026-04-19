#!/usr/bin/env python3
"""
Converts resume markdown files to HTML and PDF.

Usage:
    python3 build.py vc/resume.md          # builds vc/resume.html and vc/resume.pdf
    python3 build.py swe/resume.md         # builds swe/resume.html and swe/resume.pdf
    python3 build.py                       # builds all */resume.md found
"""

import re
import sys
import html
from pathlib import Path

CSS = """\
body {
    color: #000000;
    background: #EEEEEE;
    font: 1.05em "Times New Roman";
    line-height: 1.15;
    margin: 40px 0;
}
#resume {
    margin: 0 auto;
    max-width: 800px;
    padding: 40px 60px;
    background: #FFFFFF;
    border: 1px solid #CCCCCC;
}
h1 {
    text-transform: uppercase;
    text-align: center;
    font-size: 200%;
    margin: 0;
    padding: 0;
}
h2 {
    border-bottom: 1px solid #000000;
    text-transform: uppercase;
    font-size: 120%;
    margin: 0.8em 0 0.1em 0;
    padding: 0;
}
h3 {
    font-size: 120%;
    margin: 0.8em 0 0.1em 0;
    padding: 0;
    display: flex;
    justify-content: space-between;
}
h4 {
    font-size: 100%;
    margin: 0.8em 0 0.1em 0;
    padding: 0;
}
h5 {
    font-size: 80%;
    margin: 0.8em 0 0.1em 0;
    padding: 0;
}
p {
    margin: 0 0 0.5em 0;
    padding: 0;
}
ul {
    padding: 0;
    margin: 0 1.5em;
}
h1 + ul {
    text-align: center;
    margin: 0;
    padding: 0;
}
h1 + ul > li {
    display: inline;
    white-space: pre;
    list-style-type: none;
}
h1 + ul > li:after {
    content: "  \\2022  ";
}
h1 + ul > li:last-child:after {
    content: "";
}
h1 + ul + p {
    margin: 1em 0;
}
@media print {
    body {
        font-size: 10pt;
        margin: 0;
        padding: 0;
        background: none;
    }
    #resume {
        margin: 0;
        padding: 0;
        border: 0px;
        background: none;
    }
    a, a:link, a:visited, a:hover {
        color: #000000;
        text-decoration: underline;
    }
}
@page {
    size: letter;
    margin: 0.5in 0.8in;
}
"""


def convert_inline_md(text: str) -> str:
    """Convert inline markdown syntax to HTML."""
    # Convert markdown links [text](url) to <a> tags
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Convert email links <email@example.com> (but not <span> or other HTML tags)
    text = re.sub(r"<(\w+@[\w.]+)>", r'<a href="mailto:\1">\1</a>', text)
    # Convert -- to &ndash;
    text = re.sub(r"\s--\s", " &ndash; ", text)
    # Escape ampersands that aren't already entities or inside tags
    text = re.sub(r"&(?![\w#]+;)", "&amp;", text)
    # Convert smart quotes
    text = text.replace("\u2019", "&rsquo;")
    return text


def md_to_html(md_text: str) -> str:
    """Convert resume-flavored markdown to HTML."""
    # Strip HTML comments
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)

    lines = md_text.strip().split("\n")
    html_parts: list[str] = []
    in_list = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip blank lines
        if not line:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            i += 1
            continue

        # Headings
        heading_match = re.match(r"^(#{1,5})\s+(.*)", line)
        if heading_match:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            level = len(heading_match.group(1))
            content = convert_inline_md(heading_match.group(2).strip())
            html_parts.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # List items
        if line.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            item_content = convert_inline_md(line[2:])
            html_parts.append(f"<li>{item_content}</li>")
            i += 1
            continue

        # Paragraph text
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        line = convert_inline_md(line)
        html_parts.append(f"<p>{line}</p>")
        i += 1

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def build_html(body: str) -> str:
    """Wrap the HTML body in the full document template."""
    return f"""<html lang="en">
<head>
<meta charset="UTF-8">
<title>Roshan Narayan</title>
<style>
{CSS}
</style>
</head>
<body>
<div id="resume">
{body}
</div>
</body>
</html>
"""


def build(md_path: Path) -> None:
    """Build HTML and PDF from a markdown resume file."""
    md_text = md_path.read_text()
    body = md_to_html(md_text)
    full_html = build_html(body)

    html_path = md_path.with_suffix(".html")
    html_path.write_text(full_html)
    print(f"  HTML: {html_path}")

    # Try to generate PDF with weasyprint
    try:
        from weasyprint import HTML
        HTML(string=full_html).write_pdf(str(md_path.with_suffix(".pdf")))
        print(f"  PDF:  {md_path.with_suffix('.pdf')}")
    except ImportError:
        # Fall back to weasyprint CLI
        import subprocess
        pdf_path = md_path.with_suffix(".pdf")
        result = subprocess.run(
            ["weasyprint", str(html_path), str(pdf_path)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  PDF:  {pdf_path}")
        else:
            print(f"  PDF:  FAILED - {result.stderr.strip()}")
            print("  Install weasyprint: brew install weasyprint")


def main() -> None:
    root = Path(__file__).parent

    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        paths = sorted(root.glob("*/resume.md"))

    if not paths:
        print("No resume.md files found.")
        sys.exit(1)

    for md_path in paths:
        print(f"Building {md_path}...")
        build(md_path)


if __name__ == "__main__":
    main()
