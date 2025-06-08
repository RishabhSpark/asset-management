from typing import Any
from extractor.pdf_processing.extract_tables import extract_tables
from extractor.pdf_processing.extract_blocks import extract_blocks
from extractor.laptop_extractor import extract_laptop_information
from extractor.pdf_processing.format_invoices import format_invoices_for_llm
from app.core.logger import setup_logger

logger = setup_logger()


def run_pipeline(pdf_path: str) -> Any:
    logger.info(f"Starting pipeline for {pdf_path}...")
    print(f"Processing {pdf_path}...")

    try:
        blocks = extract_blocks(pdf_path)
        logger.info(f"Extracted {len(blocks)} text blocks from PDF.")
    except Exception as e:
        logger.error(f"Failed to extract text blocks: {e}")
        raise

    try:
        tables = extract_tables(pdf_path)
        logger.info(f"Extracted {len(tables)} tables from PDF.")
    except Exception as e:
        logger.error(f"Failed to extract tables: {e}")
        raise

    try:
        formatted_invoices = format_invoices_for_llm(blocks, tables)
        logger.info("Formatted invoice for LLM input.")
    except Exception as e:
        logger.error(f"Failed to format invoice for LLM: {e}")
        raise

    try:
        logger.info("Extracting entities from invoices.")
        invoice_info = extract_laptop_information(formatted_invoices)
        logger.info(f"Invoice Extraction Results: {invoice_info}")
        print(invoice_info)
    except Exception as e:
        logger.error(f"Failed to extract information from invoice: {e}")
        raise

    logger.info("Pipeline completed successfully.")
    return invoice_info