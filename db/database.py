from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
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
    laptop_serial_number = Column(String)
    warranty_duration = Column(Integer)
    laptop_price = Column(Float)
    quantity = Column(Integer)

def init_db():
    if not os.path.exists("laptop_database.db"):
        Base.metadata.create_all(bind=engine)
    # Always check and create new tables if needed
    Base.metadata.create_all(bind=engine)