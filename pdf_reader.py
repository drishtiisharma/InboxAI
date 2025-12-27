import warnings
import logging
import pdfplumber

warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def extract_text_from_pdf(path):
    text = ""
<<<<<<< HEAD
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
=======
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"[ERROR reading PDF: {str(e)}]"

    return " ".join(text.split())
>>>>>>> backend
