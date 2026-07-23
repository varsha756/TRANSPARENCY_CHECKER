import pdfplumber
import io

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extracts text from a PDF file uploaded via Streamlit's file_uploader.
    
    Args:
        uploaded_file: A file-like object (from st.file_uploader).
    
    Returns:
        str: Extracted text from all pages of the PDF.
    """
    text = ""
    try:
        # Ensure uploaded_file is in a format pdfplumber can read
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n"
                    text += page_text + "\n"
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text.strip()
