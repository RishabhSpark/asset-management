import os
import json
import pandas as pd
from sqlalchemy import create_engine
from db.database import SessionLocal, LaptopInvoice, LaptopItem
from app.core.logger import setup_logger

logger = setup_logger()

def export_all_laptop_invoices_json(output_path="output/assets/laptop_invoices.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    session = SessionLocal()
    logger.info("Starting export of all laptop invoices to JSON.")
    all_invoices = session.query(LaptopInvoice).all()
    export_data = []
    for inv in all_invoices:
        items = session.query(LaptopItem).filter_by(invoice_id=inv.id).all()
        laptops = []
        for item in items:
            laptops.append({
                "Lapotop Model": item.laptop_model,
                "Processor": item.processor,
                "RAM": item.ram,
                "Storage": item.storage,
                "Model Color": item.model_color,
                "Screen Size": item.screen_size,
                "Laptop OS": item.laptop_os,
                "Laptop OS Version": item.laptop_os_version,
                "Laptop Serial Number": item.laptop_serial_number,
                "Warranty Duration": item.warranty_duration,
                "Laptop Price": item.laptop_price,
                # "Quantity": item.quantity
            })
        inv_dict = {
            "Invoice Number": inv.invoice_number,
            "Order Date": inv.order_date,
            "Invoice Date": inv.invoice_date,
            "Order Number": inv.order_number,
            "Supplier (Vendor) Name": inv.supplier_name,
            "Laptops": laptops
        }
        export_data.append(inv_dict)
    session.close()
    logger.info(f"Exported {len(export_data)} laptop invoices. Writing to {output_path}")
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)
    logger.info(f"Exported {len(export_data)} laptop invoices to {output_path}")

def export_all_laptop_invoices_csv(output_path="output/assets/laptop_invoices.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    engine = create_engine("sqlite:///invoices_database.db")
    logger.info("Exporting all laptop items to CSV.")
    df = pd.read_sql("""
        SELECT i.invoice_number, i.order_date, i.invoice_date, i.order_number, i.supplier_name,
               l.laptop_model, l.processor, l.ram, l.storage, l.model_color, l.screen_size, l.laptop_os, l.laptop_os_version, l.laptop_serial_number, l.warranty_duration, l.laptop_price, l.quantity
        FROM laptop_invoices i
        JOIN laptop_items l ON i.id = l.invoice_id
    """, engine)
    df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(df)} laptop items to {output_path}")