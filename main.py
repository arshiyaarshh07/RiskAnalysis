from fastapi import FastAPI, UploadFile, File
import shutil
import os

from extractor.pdf_parser import extract_text_pdf
from extractor.ocr import extract_ocr_text
from extractor.docx_parser import extract_docx
from extractor.excel_parser import extract_excel

from utils.helpers import clean_text
from ai_engine.analyzer import analyze_text
from output.report_generator import generate_report

app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):

    try:

        file_path = os.path.join(
            UPLOAD_DIR,
            file.filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_text = ""

        if file.filename.endswith(".pdf"):

            extracted_text = extract_text_pdf(file_path)

            if len(extracted_text.strip()) < 100:
                extracted_text = extract_ocr_text(file_path)

        elif file.filename.endswith(".docx"):

            extracted_text = extract_docx(file_path)

        elif file.filename.endswith(".xlsx"):

            extracted_text = extract_excel(file_path)

        if not extracted_text:

            return {
                "error": "No evidence provided"
            }

        cleaned_text = clean_text(extracted_text)

        analysis = analyze_text(cleaned_text)

        os.makedirs("reports", exist_ok=True)

        base_name = os.path.splitext(file.filename)[0]

        report_path = f"reports/{base_name}_report.pdf"

        generate_report(
            analysis,
            report_path
        )

        return {
            "analysis": analysis,
            "report": report_path
        }

    except Exception as e:

        print("\nMAIN ERROR:\n")
        print(str(e))

        return {
            "error": str(e)
        }
