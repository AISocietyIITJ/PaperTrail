import pypdf
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


script_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(script_dir, "../../data/Resume.pdf")


def extract_text_from_pdf(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except FileNotFoundError as e:
        print(f"Error! {e.strerror}")
        return ""

# print(extract_text_from_pdf(resume_path))



