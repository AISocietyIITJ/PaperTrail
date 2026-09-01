import pypdf
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.logger import logger

script_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(script_dir, "../../data/Resume.pdf")


def extract_text_from_pdf(pdf_path):
    logger.info(f"Extracting text from PDF: {pdf_path}")

    try:
        reader = pypdf.PdfReader(pdf_path)
        logger.debug(f"PDF has {len(reader.pages)} pages")

        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text:
                logger.warning(f"No extractable text found on page {i + 1}")
                page_text = ""
            text += page_text + "\n"

        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text.strip()

    except FileNotFoundError as e:
        logger.error(f"PDF file not found: {pdf_path} | {e.strerror}")
        return ""

    except Exception:
        logger.exception(f"Unexpected error while extracting text from PDF: {pdf_path}")
        return ""

# print(extract_text_from_pdf(resume_path))



