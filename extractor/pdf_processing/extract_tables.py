import pdfplumber
from typing import List
from app.core.logger import setup_logger

logger = setup_logger()

def extract_tables(pdf_path: str) -> List[List[List[str]]]:
    """
    Extracts tables from a PDF using pdfplumber.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        List[List[List[str]]]: A list of tables, where each table is a list of rows, and each row is a list of cell values.
    """
    logger.info(f"Opening PDF file for table extraction: {pdf_path}")
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"Number of pages in PDF: {len(pdf.pages)}")
            for page_num, page in enumerate(pdf.pages, start=1):
                logger.info(f"Extracting tables from page {page_num}")
                try:
                    extracted = page.extract_tables()
                    logger.debug(f"Found {len(extracted)} tables on page {page_num}")
                    for t_idx, table in enumerate(extracted):
                        logger.debug(f"Appending table {t_idx+1} from page {page_num}")
                        tables.append(table)
                except Exception as e:
                    logger.error(f"Failed to extract tables from page {page_num}: {e}")
    except Exception as e:
        logger.error(f"Failed to open PDF file '{pdf_path}': {e}")
        raise
    logger.info(f"Extracted {len(tables)} tables from PDF")
    return tables