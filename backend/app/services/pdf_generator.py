from fpdf import FPDF


def generate_pdf_from_markdown(markdown_content: str, pdf_path: str) -> str:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.markdown_to_pdf(markdown_content)
    pdf.output(pdf_path)
    return pdf_path
