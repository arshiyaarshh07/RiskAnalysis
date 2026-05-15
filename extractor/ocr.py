import pytesseract
from PIL import Image
import fitz
import os

def extract_ocr_text(pdf_path):
    text = ""

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            pix = page.get_pixmap()

            image_path = f"temp_page_{page_num}.png"

            pix.save(image_path)

            img = Image.open(image_path)

            text += pytesseract.image_to_string(img)

            os.remove(image_path)

    except Exception as e:
        return ""

    return text