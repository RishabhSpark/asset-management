from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()
DATABASE_URL = "sqlite:///invoices_database.db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

class LaptopInvoice(Base):
    __tablename__ = "laptop_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, index=True)
    order_date = Column(String)
    invoice_date = Column(String)
    order_number = Column(String)
    supplier_name = Column(String)
    # Relationship to laptop items
    items = relationship("LaptopItem", cascade="all, delete-orphan", backref="invoice")

class LaptopItem(Base):
    __tablename__ = "laptop_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("laptop_invoices.id"))
    laptop_model = Column(String)
    processor = Column(String)
    ram = Column(String)
    storage = Column(String)
    model_color = Column(String)
    screen_size = Column(String)
    laptop_os = Column(String)
    laptop_os_version = Column(String)
    laptop_serial_number = Column(String, unique=True)
    warranty_duration = Column(Integer)
    laptop_price = Column(Float)
    created_at = Column(String, default=None)
    warranty_expiry = Column(String, nullable=True) 
    is_retired = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    # Relationship to assignments
    assignments = relationship("LaptopAssignment", cascade="all, delete-orphan", backref="user")

class LaptopAssignment(Base):
    __tablename__ = "laptop_assignments"
    id = Column(Integer, primary_key=True, index=True)
    laptop_item_id = Column(Integer, ForeignKey("laptop_items.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(String)
    unassigned_at = Column(String, nullable=True)

    laptop_item = relationship("LaptopItem", backref="assignments")

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True, index=True)
    laptop_item_id = Column(Integer, ForeignKey("laptop_items.id"))
    date = Column(String)
    description = Column(String)
    performed_by = Column(String)
    laptop_item = relationship("LaptopItem", backref="maintenance_logs")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)  # e.g., 'create', 'edit', 'delete', 'assign', 'unassign', 'retire', etc.
    entity_type = Column(String, nullable=False)  # e.g., 'User', 'LaptopItem', 'Assignment'
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who performed the action
    timestamp = Column(String, nullable=False)
    details = Column(String, nullable=True)

    user = relationship("User", backref="audit_logs")

def init_db():
    if not os.path.exists("laptop_database.db"):
        Base.metadata.create_all(bind=engine)
    # Always check and create new tables if needed
    Base.metadata.create_all(bind=engine)