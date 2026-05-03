import pdfplumber
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text = f"PDF extraction error: {e}"
    return text.strip()


def extract_text(uploaded_file) -> tuple[str, bytes, str]:
    
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes), b"", "pdf"

    elif name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")):
        return "", file_bytes, "image"

    else:
        return "", b"", "unsupported"