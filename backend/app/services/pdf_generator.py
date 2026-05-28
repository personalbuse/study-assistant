import re

from fpdf import FPDF


def generate_pdf_from_markdown(markdown_content: str, pdf_path: str) -> str:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    _render_markdown(pdf, markdown_content)
    pdf.output(pdf_path)
    return pdf_path


def _render_markdown(pdf: FPDF, md: str):
    lines = md.split("\n")
    i = 0
    in_code = False
    code_buffer = []

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if in_code:
                _render_code_block(pdf, code_buffer)
                code_buffer = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        if not line.strip():
            pdf.ln(3)
            i += 1
            continue

        stripped = line.lstrip()

        if stripped.startswith("# ") or stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 8, stripped[2:])
            _header_line(pdf, 0.8)
            pdf.ln(2)
            i += 1
            continue

        if stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 7, stripped[3:])
            _header_line(pdf, 0.4)
            pdf.ln(1)
            i += 1
            continue

        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, stripped[4:])
            pdf.ln(1)
            i += 1
            continue

        if re.match(r"^[-*]{3,}\s*$", stripped):
            y = pdf.get_y()
            pdf.set_draw_color(180, 180, 180)
            pdf.line(15, y, pdf.w - 15, y)
            pdf.ln(4)
            i += 1
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font("Helvetica", "", 10)
            x0 = pdf.get_x()
            bullet_indent = 5
            text_indent = 10
            pdf.set_x(x0 + bullet_indent)
            pdf.cell(5, 5, "•")
            pdf.set_x(x0 + text_indent)
            pdf.multi_cell(0, 5, stripped[2:])
            i += 1
            continue

        ordered = re.match(r"^\s*(\d+)\.\s+(.*)", stripped)
        if ordered:
            pdf.set_font("Helvetica", "", 10)
            x0 = pdf.get_x()
            pdf.cell(8, 5, ordered.group(1) + ".")
            pdf.multi_cell(0, 5, ordered.group(2))
            i += 1
            continue

        table_match = re.match(r"^\|(.+)\|$", stripped)
        if table_match and i + 1 < len(lines) and re.match(r"^\|[-| ]+\|$", lines[i + 1].strip()):
            rows = [stripped]
            i += 1
            while i < len(lines) and re.match(r"^\|(.+)\|$", lines[i].strip()):
                rows.append(lines[i].strip())
                i += 1
            _render_table(pdf, rows)
            continue

        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, line, markdown=True)
        i += 1

    if code_buffer:
        _render_code_block(pdf, code_buffer)


def _header_line(pdf: FPDF, thickness: float):
    y = pdf.get_y()
    pdf.set_draw_color(26, 26, 46)
    pdf.set_line_width(thickness)
    pdf.line(15, y, pdf.w - 15, y)
    pdf.set_line_width(0.2)


def _render_code_block(pdf: FPDF, lines: list):
    if not lines:
        return

    pdf.ln(2)
    line_height = 4.5
    block_height = len(lines) * line_height + 4

    if pdf.get_y() + block_height > pdf.h - 20:
        pdf.add_page()

    x0 = pdf.get_x()
    y0 = pdf.get_y()
    pdf.set_fill_color(245, 245, 245)
    pdf.set_draw_color(210, 210, 210)
    pdf.rect(x0, y0, pdf.w - 30, block_height, "DF")
    pdf.set_xy(x0 + 3, y0 + 2)

    pdf.set_font("Courier", "", 8)
    for line in lines:
        display = line if line else " "
        pdf.set_x(x0 + 3)
        pdf.cell(0, line_height, display)
        pdf.set_y(pdf.get_y() + line_height)

    pdf.set_y(y0 + block_height + 2)


def _render_table(pdf: FPDF, rows: list):
    if len(rows) < 2:
        return

    header = [c.strip() for c in rows[0].strip("|").split("|")]
    data_rows = []
    for row in rows[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) >= len(header):
            data_rows.append(cells[: len(header)])

    col_widths = [(pdf.w - 30) / max(len(header), 1)] * max(len(header), 1)

    for row_idx, cells in enumerate([header] + data_rows):
        for j, cell in enumerate(cells):
            if row_idx == 0:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(15, 52, 96)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(26, 26, 26)
                if row_idx % 2 == 0:
                    pdf.set_fill_color(249, 249, 249)
                else:
                    pdf.set_fill_color(255, 255, 255)

            pdf.cell(col_widths[j], 6, " " + cell, border=1, fill=True)
        pdf.ln()

    pdf.set_text_color(26, 26, 26)
    pdf.ln(3)
