import pdfplumber
import io

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extracts text from a PDF file uploaded via Streamlit's file_uploader.
    """
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n"
                    text += page_text + "\n"
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text.strip()


# ---------------------------------------------------------------------------
# NEW: Donation certificate generator
# ---------------------------------------------------------------------------
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def generate_donation_certificate(donor_name: str, ngo_name: str, amount, donated_at: str) -> bytes:
    """
    Generates a PDF donation certificate and returns it as raw bytes,
    so it can be handed directly to st.download_button.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Background
    c.setFillColor(colors.HexColor("#0b0f1a"))
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Border
    c.setStrokeColor(colors.HexColor("#4f8cff"))
    c.setLineWidth(3)
    c.rect(1.2 * cm, 1.2 * cm, width - 2.4 * cm, height - 2.4 * cm, fill=False, stroke=True)

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 5 * cm, "Certificate of Donation")

    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#cfd5e6"))
    c.drawCentredString(width / 2, height - 7 * cm, "This certifies that")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#6fe2a0"))
    c.drawCentredString(width / 2, height - 8.5 * cm, donor_name)

    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#cfd5e6"))
    c.drawCentredString(width / 2, height - 10 * cm, f"has generously donated Rs. {amount} to")

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.white)
    c.drawCentredString(width / 2, height - 11.5 * cm, ngo_name)

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#8b93a7"))
    c.drawCentredString(width / 2, height - 13.5 * cm, f"Donated on: {donated_at}")

    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, 3 * cm, "Thank you for supporting transparent giving.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()