import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, send_file
from db.crud import create_user, get_all_users, get_user_by_id, update_user, delete_user, assign_laptop_to_user, get_assignments_for_user, get_assignments_for_laptop, unassign_laptop
from db.database import SessionLocal, LaptopItem, LaptopAssignment, User, LaptopInvoice
from sqlalchemy.orm import joinedload
from datetime import datetime
import pandas as pd

app = Flask(__name__)

@app.route("/")
def index():
    users = get_all_users()
    return render_template("index.html", users=users)

@app.route("/users/add", methods=["GET", "POST"])
def add_user():
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        session = SessionLocal()
        # Duplicate email check
        exists = session.query(User).filter_by(email=email).first()
        if exists:
            error = "A user with this email already exists."
            session.close()
            return render_template("add_user.html", error=error)
        session.close()
        create_user(name, email)
        return redirect(url_for("index"))
    return render_template("add_user.html", error=error)

@app.route("/users/<int:user_id>")
def user_detail(user_id):
    user = get_user_by_id(user_id)
    assignments = get_assignments_for_user(user_id)
    return render_template("user_detail.html", user=user, assignments=assignments)

@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    user = get_user_by_id(user_id)
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        session = SessionLocal()
        # Duplicate email check (ignore self)
        exists = session.query(User).filter(User.email==email, User.id!=user_id).first()
        if exists:
            error = "A user with this email already exists."
            session.close()
            return render_template("edit_user.html", user=user, error=error)
        session.close()
        update_user(user_id, name, email)
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("edit_user.html", user=user, error=error)

@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user_route(user_id):
    delete_user(user_id)
    return redirect(url_for("index"))

@app.route("/laptops")
def list_laptops():
    show_unassigned = request.args.get("unassigned") == "1"
    session = SessionLocal()
    if show_unassigned:
        # Get all laptop IDs that are currently assigned
        assigned_ids = set([a.laptop_item_id for a in session.query(LaptopAssignment).filter_by(unassigned_at=None).all()])
        laptops = session.query(LaptopItem).filter(~LaptopItem.id.in_(assigned_ids), LaptopItem.is_retired == False).all()
    else:
        laptops = session.query(LaptopItem).filter(LaptopItem.is_retired == False).all()
    session.close()
    return render_template("laptops.html", laptops=laptops, show_unassigned=show_unassigned)

@app.route("/assign", methods=["GET", "POST"])
def assign_laptop():
    session = SessionLocal()
    users = session.query(User).all()
    # Only show laptops that are not assigned and not retired
    assigned_ids = set([a.laptop_item_id for a in session.query(LaptopAssignment).filter_by(unassigned_at=None).all()])
    laptops = session.query(LaptopItem).filter(~LaptopItem.id.in_(assigned_ids), LaptopItem.is_retired == False).all()
    session.close()
    error = None
    if request.method == "POST":
        user_id = int(request.form["user_id"])
        laptop_item_id = int(request.form["laptop_item_id"])
        session = SessionLocal()
        # Prevent double assignment
        active_assignment = session.query(LaptopAssignment).filter_by(laptop_item_id=laptop_item_id, unassigned_at=None).first()
        if active_assignment:
            error = "This laptop is already assigned. Please unassign it first."
            session.close()
            return render_template("assign_laptop.html", users=users, laptops=laptops, error=error)
        now = datetime.now().isoformat()
        assignment = LaptopAssignment(
            laptop_item_id=laptop_item_id,
            user_id=user_id,
            assigned_at=now,
            unassigned_at=None
        )
        session.add(assignment)
        session.commit()
        session.close()
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("assign_laptop.html", users=users, laptops=laptops, error=error)

@app.route("/unassign/<int:assignment_id>", methods=["POST"])
def unassign_laptop_route(assignment_id):
    from datetime import datetime
    session = SessionLocal()
    assignment = session.query(LaptopAssignment).filter_by(id=assignment_id).first()
    user_id = assignment.user_id if assignment else None
    if assignment and assignment.unassigned_at is None:
        assignment.unassigned_at = datetime.now().isoformat()
        session.commit()
    session.close()
    if user_id:
        return redirect(url_for("user_detail", user_id=user_id))
    return redirect(url_for("index"))

@app.route("/laptops/add", methods=["GET", "POST"])
def add_laptop():
    error = None
    if request.method == "POST":
        from datetime import datetime
        session = SessionLocal()
        def get_field(name):
            value = request.form.get(name)
            return value if value and value.strip() != '' else None
        # Required fields validation
        model = get_field("laptop_model")
        serial = get_field("laptop_serial_number")
        if not model or not serial:
            error = "Model and Serial Number are required."
            session.close()
            return render_template("add_laptop.html", error=error)
        # Unique serial number validation
        exists = session.query(LaptopItem).filter_by(laptop_serial_number=serial).first()
        if exists:
            error = "A laptop with this serial number already exists."
            session.close()
            return render_template("add_laptop.html", error=error)
        laptop = LaptopItem(
            laptop_model=model,
            processor=get_field("processor"),
            ram=get_field("ram"),
            storage=get_field("storage"),
            model_color=get_field("model_color"),
            screen_size=get_field("screen_size"),
            laptop_os=get_field("laptop_os"),
            laptop_os_version=get_field("laptop_os_version"),
            laptop_serial_number=serial,
            warranty_duration=get_field("warranty_duration"),
            laptop_price=get_field("laptop_price"),
            invoice_id=None,  # Or set to a valid invoice if needed
            created_at=datetime.now().isoformat()
        )
        session.add(laptop)
        session.commit()
        session.close()
        return redirect(url_for("list_laptops"))
    return render_template("add_laptop.html", error=error)

@app.route("/laptops/<int:laptop_id>/edit", methods=["GET", "POST"])
def edit_laptop(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    error = None
    if not laptop:
        session.close()
        return redirect(url_for("list_laptops"))
    if request.method == "POST":
        def get_field(name):
            value = request.form.get(name)
            return value if value and value.strip() != '' else None
        model = get_field("laptop_model")
        serial = get_field("laptop_serial_number")
        if not model or not serial:
            error = "Model and Serial Number are required."
            session.close()
            return render_template("edit_laptop.html", laptop=laptop, error=error)
        # Unique serial number validation (ignore self)
        exists = session.query(LaptopItem).filter(LaptopItem.laptop_serial_number==serial, LaptopItem.id!=laptop_id).first()
        if exists:
            error = "A laptop with this serial number already exists."
            session.close()
            return render_template("edit_laptop.html", laptop=laptop, error=error)
        laptop.laptop_model = model
        laptop.processor = get_field("processor")
        laptop.ram = get_field("ram")
        laptop.storage = get_field("storage")
        laptop.model_color = get_field("model_color")
        laptop.screen_size = get_field("screen_size")
        laptop.laptop_os = get_field("laptop_os")
        laptop.laptop_os_version = get_field("laptop_os_version")
        laptop.laptop_serial_number = serial
        laptop.warranty_duration = get_field("warranty_duration")
        laptop.laptop_price = get_field("laptop_price")
        session.commit()
        session.close()
        return redirect(url_for("list_laptops"))
    session.close()
    return render_template("edit_laptop.html", laptop=laptop, error=error)

@app.route("/laptops/<int:laptop_id>")
def laptop_detail(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).options(joinedload(LaptopItem.maintenance_logs)).filter_by(id=laptop_id).first()
    assignments = []
    if laptop:
        assignments = session.query(LaptopAssignment).options(joinedload(LaptopAssignment.user)).filter_by(laptop_item_id=laptop_id).all()
    session.close()
    return render_template("laptop_detail.html", laptop=laptop, assignments=assignments)

@app.route("/laptops/<int:laptop_id>/retire", methods=["POST"])
def retire_laptop(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    # Check if currently assigned
    active_assignment = session.query(LaptopAssignment).filter_by(laptop_item_id=laptop_id, unassigned_at=None).first()
    if active_assignment:
        user = session.query(User).filter_by(id=active_assignment.user_id).first()
        session.close()
        error = f"Cannot retire: Laptop is currently assigned to {user.name} ({user.email})"
        # Re-render the laptop detail page with error
        session = SessionLocal()
        laptop = session.query(LaptopItem).options(joinedload(LaptopItem.maintenance_logs)).filter_by(id=laptop_id).first()
        assignments = []
        if laptop:
            assignments = session.query(LaptopAssignment).options(joinedload(LaptopAssignment.user)).filter_by(laptop_item_id=laptop_id).all()
        session.close()
        return render_template("laptop_detail.html", laptop=laptop, assignments=assignments, error=error)
    if laptop:
        laptop.is_retired = True
        session.commit()
    session.close()
    return redirect(url_for("laptop_detail", laptop_id=laptop_id))

@app.route("/laptops/<int:laptop_id>/maintenance", methods=["GET", "POST"])
def add_maintenance_log(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    error = None
    if not laptop:
        session.close()
        return redirect(url_for("list_laptops"))
    if request.method == "POST":
        from db.database import MaintenanceLog
        from datetime import datetime
        description = request.form.get("description")
        performed_by = request.form.get("performed_by")
        if not description or not performed_by:
            error = "Description and Performed By are required."
            session.close()
            return render_template("add_maintenance.html", laptop=laptop, error=error)
        log = MaintenanceLog(
            laptop_item_id=laptop_id,
            date=datetime.now().isoformat(),
            description=description,
            performed_by=performed_by
        )
        session.add(log)
        session.commit()
        session.close()
        return redirect(url_for("laptop_detail", laptop_id=laptop_id))
    session.close()
    return render_template("add_maintenance.html", laptop=laptop, error=error)

@app.route("/replace_device/<int:assignment_id>", methods=["GET", "POST"])
def replace_device(assignment_id):
    session = SessionLocal()
    assignment = session.query(LaptopAssignment).filter_by(id=assignment_id).first()
    if not assignment or assignment.unassigned_at:
        session.close()
        return redirect(url_for("user_detail", user_id=assignment.user_id if assignment else 1))
    user_id = assignment.user_id
    old_laptop_id = assignment.laptop_item_id
    # Get all unassigned and not retired laptops
    assigned_ids = set([a.laptop_item_id for a in session.query(LaptopAssignment).filter_by(unassigned_at=None).all()])
    unassigned_laptops = session.query(LaptopItem).filter(~LaptopItem.id.in_(assigned_ids), LaptopItem.is_retired == False).all()
    error = None
    if request.method == "POST":
        new_laptop_id = int(request.form["new_laptop_id"])
        # Unassign the old device
        assignment.unassigned_at = datetime.now().isoformat()
        # Assign the new device
        new_assignment = LaptopAssignment(
            laptop_item_id=new_laptop_id,
            user_id=user_id,
            assigned_at=datetime.now().isoformat(),
            unassigned_at=None
        )
        session.add(new_assignment)
        session.commit()
        session.close()
        return redirect(url_for("user_detail", user_id=user_id))
    session.close()
    return render_template("replace_device.html", assignment=assignment, unassigned_laptops=unassigned_laptops, error=error)

@app.route("/download_invoices")
def download_invoices():
    session = SessionLocal()
    invoices = session.query(LaptopInvoice).all()
    data = []
    for invoice in invoices:
        for item in invoice.items:
            row = {
                'Invoice Number': invoice.invoice_number,
                'Order Date': invoice.order_date,
                'Invoice Date': invoice.invoice_date,
                'Order Number': invoice.order_number,
                'Supplier Name': invoice.supplier_name,
                'Laptop Model': item.laptop_model,
                'Processor': item.processor,
                'RAM': item.ram,
                'Storage': item.storage,
                'Color': item.model_color,
                'Screen Size': item.screen_size,
                'OS': item.laptop_os,
                'OS Version': item.laptop_os_version,
                'Serial Number': item.laptop_serial_number,
                'Warranty Duration': item.warranty_duration,
                'Price': item.laptop_price,
                'Created At': item.created_at,
                'Warranty Expiry': item.warranty_expiry,
                'Is Retired': item.is_retired
            }
            data.append(row)
    session.close()
    import os
    import pandas as pd
    # Ensure output/assets directory exists
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'assets')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "laptop_invoices_download.xlsx")
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
