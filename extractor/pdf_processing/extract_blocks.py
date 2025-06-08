import fitz
from typing import List
from app.core.logger import setup_logger

logger = setup_logger()

def extract_blocks(pdf_path: str) -> List[str]:
    """
    Extracts layout-aware text blocks from a PDF using PyMuPDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        List[str]: A list of extracted text blocks, each representing a logical section or paragraph from the PDF.
    """
    logger.info(f"Opening PDF file: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF file '{pdf_path}': {e}")
        raise
    
    all_blocks = []
    logger.info(f"Number of pages in PDF: {len(doc)}")

    for page_num, page in enumerate(doc, start=1):
        logger.info(f"Processing page {page_num}")
        try:
            blocks = page.get_text("dict")["blocks"]
        except Exception as e:
            logger.error(f"Failed to extract blocks from page {page_num}: {e}")
            continue

        logger.debug(f"Found {len(blocks)} blocks on page {page_num}")
        for b_idx, b in enumerate(blocks):
            if "lines" in b:
                lines = []
                for l_idx, l in enumerate(b["lines"]):
                    spans = [s["text"] for s in l["spans"] if s["text"].strip()]
                    if spans:
                        lines.append(" ".join(spans))
                if lines:
                    logger.debug(f"Block {b_idx} on page {page_num} has {len(lines)} lines")
                    all_blocks.append("\n".join(lines))

    logger.info(f"Extracted {len(all_blocks)} text blocks from PDF")
    return all_blocks