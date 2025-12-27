from PIL import Image
import pytesseract

<<<<<<< HEAD

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return ""
=======
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)

        # Improve OCR accuracy
        custom_config = r"--oem 3 --psm 6"

        text = pytesseract.image_to_string(
            image,
            lang="eng",
            config=custom_config
        )

        return text.strip()

    except Exception as e:
        return f"[ERROR reading image: {str(e)}]"
>>>>>>> backend
