from fastapi import FastAPI, HTTPException, Form, UploadFile, File
import os
import logging
import tempfile
import docx2pdf
from docx import Document
from modules.delhi import extract_delhi_dsi
from modules.chennai import extract_data_f1f2, extract_data_cocr

logging.basicConfig(level=logging.INFO)

app = FastAPI()

def convert_to_pdf(input_file: str):
    """Converts .doc or .docx files to .pdf for processing."""
    try:
        logging.info(f"Starting conversion of {input_file} to PDF.")
        if not os.path.isfile(input_file):
            logging.error(f"File {input_file} does not exist.")
            return None

        file_extension = os.path.splitext(input_file)[1].lower()
        base_name = os.path.splitext(input_file)[0]

        if file_extension == '.docx':
            pdf_file = f"{base_name}.pdf"
            docx2pdf.convert(input_file, pdf_file)
            logging.info(f".docx file converted to .pdf: {pdf_file}")
            return pdf_file  # Return the path to the new PDF file

        elif file_extension == '.pdf':
            logging.info(f"File is already a PDF: {input_file}")
            return input_file  # If already a PDF, return as is

        else:
            logging.error(f"Unsupported file extension: {file_extension}")
            return None

    except Exception as e:
        logging.error(f"Error converting file {input_file}: {e}")
        return None

@app.post("/process-file")
async def process_file(
    location: str = Form(...),
    parser_type: str = Form(""),
    file: UploadFile = File(...)
):
    # Save uploaded file temporarily for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name

    # Convert file to PDF if necessary
    pdf_file = convert_to_pdf(temp_file_path)
    if not pdf_file:
        os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail="File could not be converted or does not exist.")

    # Select the appropriate parser based on location and parser type
    try:
        if location.lower() == "delhi":
            logging.info(f"Using Delhi parser for {pdf_file}")
            result = extract_delhi_dsi(pdf_file)
            return {"message": "File processed with Delhi parser", "result": result}

        elif location.lower() == "chennai":
            if parser_type.lower() == "f1f2":
                logging.info(f"Using Chennai F1F2 parser for {pdf_file}")
                result = extract_data_f1f2(pdf_file)
                return {"message": "File processed with Chennai F1F2 parser", "result": result}

            elif parser_type.lower() == "cocr":
                logging.info(f"Using Chennai COCR parser for {pdf_file}")
                result = extract_data_cocr(pdf_file)
                return {"message": "File processed with Chennai COCR parser", "result": result}
    finally:
        # Clean up temporary files
        os.remove(temp_file_path)
        if pdf_file != temp_file_path:  # Only remove if a conversion happened
            os.remove(pdf_file)

    # If the input doesn't match expected values
    raise HTTPException(status_code=400, detail="Invalid location or parser type provided.")
