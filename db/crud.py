from db.database import DriveFile, SessionLocal, LaptopInvoice, LaptopItem, User, LaptopAssignment
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
            serial = serials[i] if i < len(serials) else None
            # Check for duplicate serial number
            if serial:
                existing_laptop = session.query(LaptopItem).filter_by(laptop_serial_number=serial).first()
                if existing_laptop:
                    # Update existing laptop fields
                    existing_laptop.invoice_id = invoice.id
                    existing_laptop.laptop_model = item.get("Lapotop Model")
                    existing_laptop.processor = item.get("Processor")
                    existing_laptop.ram = item.get("RAM")
                    existing_laptop.storage = item.get("Storage")
                    existing_laptop.model_color = item.get("Model Color")
                    existing_laptop.screen_size = item.get("Screen Size")
                    existing_laptop.laptop_os = item.get("Laptop OS")
                    existing_laptop.laptop_os_version = item.get("Laptop OS Version")
                    existing_laptop.warranty_duration = item.get("Warranty Duration")
                    existing_laptop.laptop_price = item.get("Laptop Price")
                    continue  # Don't add a new one
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
                laptop_serial_number=serial,
                warranty_duration=item.get("Warranty Duration"),
                laptop_price=item.get("Laptop Price")
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

def soft_delete_user(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    if not user or not user.is_active:
        session.close()
        return False
    user.is_active = False
    session.commit()
    session.close()
    return True

def soft_delete_laptop(laptop_id: int) -> bool:
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    if not laptop or not laptop.is_active:
        session.close()
        return False
    laptop.is_active = False
    session.commit()
    session.close()
    return 

def upsert_drive_files_sqlalchemy(files_data: list[dict]):
    """
    Upserts (updates or inserts) DriveFile records using SQLAlchemy.
    Deletes records from the DB that are not in the provided files_data list based on ID.

    Args:
        files_data: A list of dictionaries, where each dictionary
                    represents a file and contains 'id', 'name',
                    and 'modifiedTime' (as an ISO 8601 string).
    """
    session = SessionLocal()
    try:
        # Get all current DB file IDs for efficient deletion check later
        current_db_file_ids = {db_file.id for db_file in session.query(DriveFile.id).all()}
        
        processed_ids = set()

        for file_data in files_data:
            file_id = file_data['id']
            file_name = file_data['name']
            processed_ids.add(file_id)

            try:
                modified_time_str = file_data.get('modifiedTime')
                # Ensure Z is handled correctly for UTC, or timezone info is present
                if modified_time_str:
                    if modified_time_str.endswith('Z'):
                        last_edited_dt = datetime.fromisoformat(modified_time_str[:-1] + '+00:00')
                    else:
                        last_edited_dt = datetime.fromisoformat(modified_time_str)
                else:
                    last_edited_dt = None
            except ValueError as ve:
                # Log this error: print(f"ValueError parsing date for file {file_id}: {ve}")
                last_edited_dt = None # Or handle as appropriate

            existing_file = session.query(DriveFile).filter_by(id=file_id).first()

            if existing_file:
                # Update if name or modifiedTime is different
                if existing_file.name != file_name or existing_file.last_edited != last_edited_dt:
                    existing_file.name = file_name
                    existing_file.last_edited = last_edited_dt
            else:
                # Insert new file
                new_file = DriveFile(
                    id=file_id,
                    name=file_name,
                    last_edited=last_edited_dt
                )
                session.add(new_file)

        # Delete files from DB that are not in the incoming list
        ids_to_delete = current_db_file_ids - processed_ids
        if ids_to_delete:
            session.query(DriveFile).filter(DriveFile.id.in_(ids_to_delete)).delete(synchronize_session=False)
        
        session.commit()
    except Exception as e:
        session.rollback()
        # Consider logging the error e, e.g., logger.error(f"Error in upsert_drive_files_sqlalchemy: {e}")
        raise
    finally:
        session.close()


def get_all_drive_files():
    """
    Returns a dict mapping file name to (last_edited, id) for all files in the drive_files table.
    """
    session = SessionLocal()
    try:
        files = session.query(DriveFile).all()
        # Map: name -> (last_edited, id)
        return {f.name: (f.last_edited, f.id) for f in files}
    finally:
        session.close()


def delete_invoice_by_drive_file_id(file_id):
    """
    Deletes all PO-related data (purchase order, milestones, payment schedule) for a given drive file id.
    Assumes PO id is the same as drive file id or can be mapped (adjust as needed).
    """
    session = SessionLocal()
    try:
        # Find all POs linked to this drive file id (assuming id == file_id)
        po = session.query(LaptopItem).filter_by(id=file_id).first()
        if po:
            # Delete related milestones and payment schedules (cascade should handle if set)
            session.delete(po)
            session.commit()
    finally:
        session.close()