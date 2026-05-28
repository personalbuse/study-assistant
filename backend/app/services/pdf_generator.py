import markdown
from weasyprint import HTML, CSS


def generate_pdf_from_markdown(markdown_content: str, pdf_path: str) -> str:
    html_content = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code", "codehilite"],
    )

    css = CSS(
        string="""
        @page { margin: 2.5cm 2cm; size: letter; }
        body {
            font-family: 'DejaVu Serif', 'Liberation Serif', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #1a1a1a;
        }
        h1 {
            font-size: 22pt;
            color: #1a1a2e;
            border-bottom: 3px solid #1a1a2e;
            padding-bottom: 6px;
            margin-top: 30px;
        }
        h2 {
            font-size: 16pt;
            color: #16213e;
            border-bottom: 1px solid #ccc;
            padding-bottom: 4px;
            margin-top: 25px;
        }
        h3 {
            font-size: 13pt;
            color: #0f3460;
            margin-top: 20px;
        }
        p { margin: 8px 0; text-align: justify; }
        code {
            font-family: 'DejaVu Sans Mono', 'Liberation Mono', monospace;
            font-size: 10pt;
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
        }
        pre {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
            overflow-x: auto;
        }
        pre code { background: none; padding: 0; }
        ul, ol { margin: 8px 0 8px 20px; }
        li { margin: 4px 0; }
        blockquote {
            border-left: 4px solid #0f3460;
            padding-left: 15px;
            margin: 15px 0;
            color: #444;
            font-style: italic;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #bbb;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background: #0f3460;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) { background: #f9f9f9; }
        strong { color: #0f3460; }
        a { color: #0f3460; text-decoration: none; }
        hr { border: none; border-top: 2px solid #ccc; margin: 20px 0; }
    """
    )

    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[css])
    return pdf_path
