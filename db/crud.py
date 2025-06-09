from db.database import SessionLocal, LaptopInvoice, LaptopItem, User, LaptopAssignment
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import joinedload

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

def create_user(name: str, email: str) -> User:
    session = SessionLocal()
    user = User(name=name, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user

def get_user_by_email(email: str) -> Optional[User]:
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    session.close()
    return user

def get_user_by_id(user_id: int) -> Optional[User]:
    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()
    return user

def get_all_users() -> List[User]:
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users

def update_user(user_id: int, name: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        session.close()
        return None
    if name:
        user.name = name
    if email:
        user.email = email
    session.commit()
    session.refresh(user)
    session.close()
    return user

def delete_user(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        session.close()
        return False
    session.delete(user)
    session.commit()
    session.close()
    return True

def assign_laptop_to_user(laptop_item_id: int, user_id: int, assigned_at: Optional[str] = None) -> LaptopAssignment:
    session = SessionLocal()
    if assigned_at is None:
        assigned_at = datetime.now().isoformat()
    assignment = LaptopAssignment(laptop_item_id=laptop_item_id, user_id=user_id, assigned_at=assigned_at)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    session.close()
    return assignment

def get_assignments_for_user(user_id: int) -> List[LaptopAssignment]:
    session = SessionLocal()
    assignments = session.query(LaptopAssignment)\
        .options(joinedload(LaptopAssignment.laptop_item))\
        .filter_by(user_id=user_id).all()
    session.close()
    return assignments

def get_assignments_for_laptop(laptop_item_id: int) -> List[LaptopAssignment]:
    session = SessionLocal()
    assignments = session.query(LaptopAssignment).filter_by(laptop_item_id=laptop_item_id).all()
    session.close()
    return assignments

def unassign_laptop(assignment_id: int) -> bool:
    session = SessionLocal()
    assignment = session.query(LaptopAssignment).filter_by(id=assignment_id).first()
    if not assignment:
        session.close()
        return False
    session.delete(assignment)
    session.commit()
    session.close()
    return True
