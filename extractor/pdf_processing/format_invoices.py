from typing import List
from app.core.logger import setup_logger

logger = setup_logger()

def format_invoices_for_llm(text_blocks: List[str], tables: List[List[List[str]]]) -> str:
    """
    Format extracted text blocks and tables into a clean plain-text string
    suitable for input to an LLM.

    Args:
        text_blocks: List of text blocks extracted from the PDF.
        tables: List of tables, where each table is a list of rows,
                and each row is a list of cell strings.

    Returns:
        A single formatted string combining all text and tables for LLM consumption.
    """
    logger.info(f"Formatting {len(text_blocks)} text blocks and {len(tables)} tables for LLM input.")
    
    formatted_text = "\n\n".join(text_blocks)
    logger.debug("Formatted text blocks.")
    
    # Format each table into a readable plain text table
    formatted_tables = ""
    for idx, table in enumerate(tables, start=1):
        logger.debug(f"Formatting table {idx} with {len(table)} rows.")
        table_rows = ["\t".join(map(str, row)) for row in table]
        table_str = "\n".join(table_rows)
        formatted_tables += f"\n\nTable {idx}:\n{table_str}"

    logger.info("Finished formatting text and tables for LLM.")

    return formatted_text + formatted_tables