from db.database import SessionLocal, LaptopInvoice, LaptopItem
from typing import Dict, Any

def insert_or_replace_laptop_invoice(invoice_dict: Dict[str, Any]) -> None:
    session = SessionLocal()
    invoice_number = invoice_dict.get("Invoice Number")

    # delete if exists (cascades to items)
    existing = session.query(LaptopInvoice).filter_by(invoice_number=invoice_number).first()
    if existing:
        session.delete(existing)
        session.commit()

    # insert main invoice
    invoice = LaptopInvoice(
        invoice_number=invoice_dict.get("Invoice Number"),
        order_date=invoice_dict.get("Order Date"),
        invoice_date=invoice_dict.get("Invoice Date"),
        order_number=invoice_dict.get("Order Number"),
        supplier_name=invoice_dict.get("Supplier (Vendor) Name")
    )
    session.add(invoice)
    session.flush()  # get invoice.id

    # insert all laptop items
    for item in invoice_dict.get("Laptops", []):
        quantity = item.get("Quantity", 1)
        serial_numbers = item.get("Laptop Serial Number")
        # If serial_numbers is a list, use it, else make a list of Nones or repeat the value
        if isinstance(serial_numbers, list):
            serials = serial_numbers
        elif serial_numbers is not None:
            serials = [serial_numbers] * quantity
        else:
            serials = [None] * quantity
        for i in range(quantity):
            laptop_item = LaptopItem(
                invoice_id=invoice.id,
                laptop_model=item.get("Lapotop Model"),
                processor=item.get("Processor"),
                ram=item.get("RAM"),
                storage=item.get("Storage"),
                model_color=item.get("Model Color"),
                screen_size=item.get("Screen Size"),
                laptop_os=item.get("Laptop OS"),
                laptop_os_version=item.get("Laptop OS Version"),
                laptop_serial_number=serials[i] if i < len(serials) else None,
                warranty_duration=item.get("Warranty Duration"),
                laptop_price=item.get("Laptop Price"),
                quantity=1
            )
            session.add(laptop_item)
    session.commit()
    session.close()

def get_laptop_invoice(invoice_number: str):
    session = SessionLocal()
    try:
        inv = session.query(LaptopInvoice).filter_by(invoice_number=invoice_number).first()
        if not inv:
            return None
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
                "Quantity": item.quantity
            })
        return {
            "Invoice Number": inv.invoice_number,
            "Order Date": inv.order_date,
            "Invoice Date": inv.invoice_date,
            "Order Number": inv.order_number,
            "Supplier (Vendor) Name": inv.supplier_name,
            "Laptops": laptops
        }
    finally:
        session.close()
