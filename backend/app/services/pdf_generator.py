import re
import traceback

from fpdf import FPDF


def generate_pdf_from_markdown(markdown_content: str, pdf_path: str) -> str:
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        _render_markdown(pdf, markdown_content)
        pdf.output(pdf_path)
    except Exception as e:
        print(f"[WARN] PDF render failed, generating fallback: {e}")
        traceback.print_exc()
        _generate_fallback_pdf(pdf_path)
    return pdf_path


def _generate_fallback_pdf(pdf_path: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, "Documento generado por StudiedUp")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(10)
    pdf.multi_cell(0, 6, "El contenido no pudo renderizarse como PDF. Usa /docs list para ver el archivo .md original.")
    pdf.output(pdf_path)


def _render_markdown(pdf: FPDF, md: str):
    lines = md.split("\n")
    i = 0
    in_code = False
    code_buffer = []

    while i < len(lines):
        line = lines[i]
        pdf.set_x(pdf.l_margin)

        try:
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

            if stripped.startswith("# "):
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
                pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
                pdf.ln(4)
                i += 1
                continue

            if stripped.startswith("- ") or stripped.startswith("* "):
                pdf.set_font("Helvetica", "", 10)
                x0 = pdf.get_x()
                pdf.set_x(x0 + 5)
                pdf.cell(5, 5, "\u2022")
                pdf.set_x(x0 + 12)
                pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 12, 5, stripped[2:])
                i += 1
                continue

            ordered = re.match(r"^\s*(\d+)\.\s+(.*)", stripped)
            if ordered:
                pdf.set_font("Helvetica", "", 10)
                num_text = ordered.group(1) + "."
                num_w = pdf.get_string_width(num_text) + 2
                pdf.cell(num_w, 5, num_text)
                remaining_w = pdf.w - pdf.get_x() - pdf.r_margin
                pdf.multi_cell(remaining_w, 5, ordered.group(2))
                i += 1
                continue

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, line)
            i += 1

        except Exception as e:
            print(f"[WARN] Skipping malformed markdown line {i}: {e}")
            print(f"       Line content: {line[:100]}")
            i += 1

    if code_buffer:
        _render_code_block(pdf, code_buffer)


def _header_line(pdf: FPDF, thickness: float):
    y = pdf.get_y()
    pdf.set_draw_color(26, 26, 46)
    pdf.set_line_width(thickness)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.set_line_width(0.2)


def _render_code_block(pdf: FPDF, lines: list):
    if not lines:
        return

    pdf.ln(2)
    lh = 4.5
    bh = len(lines) * lh + 4

    if pdf.get_y() + bh > pdf.h - 20:
        pdf.add_page()

    x0 = pdf.l_margin
    y0 = pdf.get_y()
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_fill_color(245, 245, 245)
    pdf.set_draw_color(210, 210, 210)
    pdf.rect(x0, y0, w, bh, "DF")
    pdf.set_font("Courier", "", 8)

    for j, line in enumerate(lines):
        pdf.set_xy(x0 + 3, y0 + 2 + j * lh)
        pdf.cell(w - 6, lh, line if line else " ")

    pdf.set_y(y0 + bh + 2)
