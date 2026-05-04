"""
Generate a professional HTML report from rapport.md.
Mermaid diagrams render as real visual diagrams via Mermaid.js CDN.

Usage: py docs/generate_pdf.py
Then open rapport.html in Chrome → Ctrl+P → Save as PDF
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_report():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(script_dir, 'rapport.md')
    html_path = os.path.join(script_dir, 'rapport.html')

    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Manual markdown → HTML conversion that preserves mermaid blocks
    html_body = convert_md_to_html(md_text)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Smart Parking System — Project Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #1e293b;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 40px;
            background: #fff;
        }}

        /* ── Cover ────────────────────────────── */
        .cover {{
            text-align: center;
            padding: 50px 30px;
            margin-bottom: 40px;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0ea5e9 100%);
            border-radius: 16px;
            color: white;
            page-break-after: always;
        }}
        .cover h1 {{
            font-size: 32pt;
            font-weight: 700;
            border: none;
            color: white;
            margin-bottom: 10px;
        }}
        .cover .subtitle {{
            font-size: 14pt;
            opacity: 0.85;
            margin-bottom: 5px;
        }}
        .cover .meta {{
            font-size: 11pt;
            opacity: 0.65;
            margin-top: 20px;
        }}

        /* ── Headings ─────────────────────────── */
        h1 {{
            color: #0f172a;
            font-size: 22pt;
            font-weight: 700;
            border-bottom: 3px solid #0ea5e9;
            padding-bottom: 8px;
            margin: 35px 0 15px 0;
        }}
        h2 {{
            color: #1e3a5f;
            font-size: 15pt;
            font-weight: 600;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 6px;
            margin: 30px 0 12px 0;
        }}
        h3 {{
            color: #334155;
            font-size: 12pt;
            font-weight: 600;
            margin: 20px 0 8px 0;
        }}

        /* ── Tables ───────────────────────────── */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 9.5pt;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        th {{
            background: linear-gradient(135deg, #0f172a, #1e3a5f);
            color: white;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 9px 14px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        tr:hover {{
            background-color: #eff6ff;
        }}

        /* ── Code ─────────────────────────────── */
        code {{
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Fira Code', monospace;
            font-size: 9.5pt;
            color: #0f172a;
        }}
        pre {{
            background: #0f172a;
            color: #e2e8f0;
            padding: 18px;
            border-radius: 10px;
            overflow-x: auto;
            font-size: 9pt;
            line-height: 1.5;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        }}
        pre code {{
            background: none;
            padding: 0;
            color: #e2e8f0;
        }}

        /* ── Mermaid diagrams ─────────────────── */
        .mermaid {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #f8fafc;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }}

        /* ── Misc ─────────────────────────────── */
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 30px 0;
        }}
        p {{
            margin: 8px 0;
        }}
        ul, ol {{
            margin: 8px 0 8px 25px;
        }}
        li {{
            margin: 4px 0;
        }}
        strong {{
            color: #0f172a;
        }}

        /* ── Print ────────────────────────────── */
        @media print {{
            body {{ padding: 0; }}
            .cover {{ page-break-after: always; }}
            pre {{ box-shadow: none; border: 1px solid #ccc; }}
            .mermaid {{ border: 1px solid #ccc; }}
        }}
    </style>
</head>
<body>

    <div class="cover">
        <h1>🅿️ Smart Parking System</h1>
        <div class="subtitle">Automated License Plate Recognition & Gate Control</div>
        <div class="subtitle">Project Report</div>
        <div class="meta">ISI — Institut Supérieur d'Informatique</div>
        <div class="meta">Arduino · Flask · OCR · SocketIO · SQLite</div>
    </div>

    {html_body}

    <hr>
    <p style="text-align:center; color:#94a3b8; font-size:9pt; margin-top:30px;">
        Smart Parking System — Project Report
    </p>

    <!-- Mermaid.js for rendering diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#0ea5e9',
                primaryTextColor: '#0f172a',
                primaryBorderColor: '#1e3a5f',
                lineColor: '#64748b',
                secondaryColor: '#f1f5f9',
                tertiaryColor: '#eff6ff',
                fontSize: '13px'
            }}
        }});
    </script>
</body>
</html>"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)

    print(f"✅ Report generated: {html_path}")
    print(f"")
    print(f"   To get a PDF:")
    print(f"   1. Open {html_path} in Chrome")
    print(f"   2. Wait for diagrams to render")
    print(f"   3. Press Ctrl+P → 'Save as PDF'")
    print(f"   4. Set margins to 'None' for best results")


def convert_md_to_html(md_text):
    """Convert markdown to HTML, preserving mermaid blocks as <div class='mermaid'>."""
    lines = md_text.split('\n')
    html_parts = []
    i = 0
    in_code = False
    code_lang = ''
    code_content = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # Fenced code blocks
        if line.strip().startswith('```') and not in_code:
            # Flush any table
            if in_table:
                html_parts.append(render_table(table_rows))
                table_rows = []
                in_table = False

            code_lang = line.strip()[3:].strip()
            in_code = True
            code_content = []
            i += 1
            continue

        if line.strip() == '```' and in_code:
            content = '\n'.join(code_content)
            if code_lang == 'mermaid':
                html_parts.append(f'<div class="mermaid">\n{content}\n</div>')
            else:
                escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<pre><code>{escaped}</code></pre>')
            in_code = False
            code_lang = ''
            code_content = []
            i += 1
            continue

        if in_code:
            code_content.append(line)
            i += 1
            continue

        # Table rows
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                if table_rows:
                    html_parts.append(render_table(table_rows))
                    table_rows = []
                in_table = True
            table_rows.append(line)
            i += 1
            continue
        else:
            if in_table:
                html_parts.append(render_table(table_rows))
                table_rows = []
                in_table = False

        # Horizontal rule
        if re.match(r'^---+$', line.strip()):
            html_parts.append('<hr>')
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = inline_format(m.group(2))
            html_parts.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue

        # Unordered list
        if re.match(r'^\s*[-*]\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]):
                item_text = re.sub(r'^\s*[-*]\s+', '', lines[i])
                list_items.append(f'<li>{inline_format(item_text)}</li>')
                i += 1
            html_parts.append('<ul>' + ''.join(list_items) + '</ul>')
            continue

        # Empty line
        if line.strip() == '':
            i += 1
            continue

        # Paragraph
        html_parts.append(f'<p>{inline_format(line)}</p>')
        i += 1

    # Flush remaining table
    if in_table:
        html_parts.append(render_table(table_rows))

    return '\n'.join(html_parts)


def render_table(rows):
    """Convert markdown table rows to HTML table."""
    if len(rows) < 2:
        return ''

    html = '<table>\n'

    # Header
    cells = [c.strip() for c in rows[0].strip('|').split('|')]
    html += '<thead><tr>'
    for cell in cells:
        html += f'<th>{inline_format(cell)}</th>'
    html += '</tr></thead>\n'

    # Body (skip separator row)
    html += '<tbody>\n'
    for row in rows[2:]:  # skip header + separator
        cells = [c.strip() for c in row.strip('|').split('|')]
        html += '<tr>'
        for cell in cells:
            html += f'<td>{inline_format(cell)}</td>'
        html += '</tr>\n'
    html += '</tbody></table>\n'

    return html


def inline_format(text):
    """Apply inline markdown formatting: bold, code, links, images."""
    # Code (backticks) — do first to avoid conflicts
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Images (must come before links)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%; border-radius:8px; margin:15px 0; box-shadow:0 2px 4px rgba(0,0,0,0.1);">', text)
    # Links
    text = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


if __name__ == '__main__':
    generate_report()
