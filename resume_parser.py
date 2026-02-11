import fitz
import io
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor


def _extract_single_pdf(args: Tuple[int, bytes]) -> Tuple[int, str]:
    """
    Extract text from one PDF.
    Returns (index, extracted_text)
    """
    index, pdf_bytes = args

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pages_text = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text.strip())

    doc.close()

    return index, "\n".join(pages_text)


def extract_text_from_pdf_bytes_parallel(pdf_bytes_list: List[bytes]) -> Dict[str, str]:
    """
    Parallel PDF extraction with ordering
    """
    indexed_inputs = list(enumerate(pdf_bytes_list, start=1))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(_extract_single_pdf, indexed_inputs))

    
    results.sort(key=lambda x: x[0])

    extracted_data = {}
    for index, text in results:
        resume_id = f"R-{index:03d}"
        extracted_data[resume_id] = text

    return extracted_data
