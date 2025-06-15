from db.crud import insert_or_replace_laptop_invoice
from db.database import init_db
from extractor.run_extraction import run_pipeline
from extractor.export import export_all_laptop_invoices_json, export_all_laptop_invoices_csv

if __name__ == "__main__":
    init_db() 

    pdf_paths = [
        "invoices/laptop_1.pdf",
        "invoices/laptop_2.pdf"
    ]
    
    print("--- Starting PDF Extraction and Database Storage ---")
    for pdf_path in pdf_paths:
        print(f"Processing PDF: {pdf_path}")
        pdf_text = run_pipeline(pdf_path) 
        if pdf_text: 
            insert_or_replace_laptop_invoice(pdf_text) 
        else:
            print(f"Warning: No data extracted from {pdf_path}. Skipping database insertion for this file.")
    print("--- PDF Extraction and Database Storage Complete ---")

    print("\n--- Exporting Data to JSON and CSV ---")
    export_all_laptop_invoices_json() 
    export_all_laptop_invoices_csv()
    print("--- Data Export Complete ---")