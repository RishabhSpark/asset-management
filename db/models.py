from sqlalchemy import Table, Column, String, Float, Integer, MetaData, ForeignKey

metadata = MetaData()

laptop_invoices = Table(
    'laptop_invoices', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('invoice_number', String, unique=True, index=True),
    Column('order_date', String),
    Column('invoice_date', String),
    Column('order_number', String),
    Column('supplier_name', String),
    Column('laptop_model', String),
    Column('processor', String),
    Column('ram', String),
    Column('storage', String),
    Column('model_color', String),
    Column('screen_size', String),
    Column('laptop_os', String),
    Column('laptop_os_version', String),
    Column('laptop_serial_number', String),
    Column('warranty_duration', Integer),
    Column('laptop_price', Float),
    Column('quantity', Integer),
)

laptop_items = Table(
    'laptop_items', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('invoice_id', Integer, ForeignKey('laptop_invoices.id')),
    Column('laptop_model', String),
    Column('processor', String),
    Column('ram', String),
    Column('storage', String),
    Column('model_color', String),
    Column('screen_size', String),
    Column('laptop_os', String),
    Column('laptop_os_version', String),
    Column('laptop_serial_number', String),
    Column('warranty_duration', Integer),
    Column('laptop_price', Float),
    Column('quantity', Integer),
)
