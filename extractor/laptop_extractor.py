import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from app.core.logger import setup_logger
from typing import Any, Dict

logger = setup_logger()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set in environment variables.")
    raise ValueError("GEMINI_API_KEY not set in environment variables.")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def extract_laptop_information(invoice_text: str) -> Dict[str, Any]:
    logger.info("Starting extraction of laptop invoice details from invoice text.")

    prompt = f"""
    You are an assistant that extracts structured data from invoices (especially laptops).

    Extract these common fields exactly at the invoice level:
- Invoice Number: a string
- Order Date: a date in the format DD-MM-YYYY
- Invoice Date: a date in the format DD-MM-YYYY
- Order Number: a string
- Supplier (Vendor) Name: a string

Then, extract a list of laptops in the invoice, each with these fields:
- Lapotop Model: a string
- Processor: a string
- RAM: a string
- Storage: a string
- Model Color: a string
- Screen Size: a string
- Laptop OS: a string
- Laptop OS Version: a string
- Laptop Serial Number: a string
- Warranty Duration: an integer in months
- Laptop Price: a number (in INR), should be the price of only one laptop and not the total price
- Quantity: an integer representing the number of this laptop in the invoice

RULES:
1. The output should be a valid JSON object.
2. The JSON object should contain all the invoice fields above, and a key 'Laptops' which is a list of laptop objects as described.
3. If a field is not present in the text, it should be set to null.
4. The JSON object should be formatted with proper indentation.
5. Do not include any additional text or explanations outside the JSON object.
6. The details should be extracted from the provided Purchase Order text.
7. If the Purchase Order text does not contain any of the fields, set those fields to null in the JSON object.
8. Do not think about the context of the invoice text, just extract the fields as they are in the format mentioned.

Return only a valid JSON object inside markdown code block, like this:

```json
{{ ... }}
```

Invoice text:
\"\"\"
{invoice_text}
\"\"\"
"""
    logger.debug("Sending prompt to Gemini model.")
    response = model.generate_content(prompt)

    raw_response = response.candidates[0].content.parts[0].text.strip()
    logger.debug("Received response from Gemini model.")

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
    if not match:
        logger.error("Gemini response did not contain valid JSON block.")
        logger.debug(f"Raw Gemini response: {raw_response}")
        raise ValueError("Gemini response did not contain valid JSON block")

    json_str = match.group(1)

    try:
        result = json.loads(json_str)
        logger.info("Successfully extracted key information from invoices.")
        return result
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from Gemini response.")
        logger.debug(f"Raw JSON that failed parsing: {json_str}")
        raise e