import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy.orm import joinedload
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from flask import Flask, render_template, request, redirect, url_for, send_file, session,flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from db.database import SessionLocal, LaptopItem, LaptopAssignment, User, LaptopInvoice, MaintenanceLog
from db.crud import create_user, get_all_users, get_user_by_id, update_user, soft_delete_user, soft_delete_laptop, get_assignments_for_user

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecret123') 
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CLIENT_SECRETS_FILE = 'client_secret.json'

USERS = {}
for i in range(1, 10): 
    username = os.getenv(f'USER_{i}_NAME')
    password = os.getenv(f'USER_{i}_PASSWORD')
    if username and password:
        USERS[username] = password  


def build_credentials(creds_dict):
    return Credentials(**creds_dict)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def load_logged_in_user():
    g.user = None
    if 'username' in session:
        g.user = session['username']


@app.route("/")
def index():
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():

    if "logged_in" in session and session['logged_in']:
        return render_template('index.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USERS and check_password_hash(USERS[username], password):
            session['logged_in'] = True
            session['username'] = username
            flash(f'Logged in successfully as {username}!', 'success')

            return render_template('index.html')
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('credentials', None)
    flash('You have been logged out.', 'info')
    session.clear()
    return redirect(url_for('login'))


@app.route('/authorize')
@login_required
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)


@app.route('/oauth2callback')
@login_required
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = creds_to_dict(creds)
    users = [u for u in get_all_users() if u.is_active]
    return redirect(url_for('users'))


@app.route('/users')
@login_required
def users():

    users = [u for u in get_all_users() if u.is_active]
    return render_template("users.html", users=users)


@app.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    if 'credentials' not in session:
        return redirect('authorize')
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        db_session = SessionLocal()
        # Duplicate email check
        exists = db_session.query(User).filter_by(email=email).first()
        if exists:
            error = "A user with this email already exists."
            db_session.close()
            return render_template("add_user.html", error=error)
        db_session.close()
        create_user(name, email)
        return redirect(url_for("users"))
    return render_template("add_user.html", error=error)


@app.route("/users/<int:user_id>")
@login_required
def user_detail(user_id):
    if 'credentials' not in session:
        return redirect('authorize')
    user = get_user_by_id(user_id)
    assignments = get_assignments_for_user(user_id)
    return render_template("user_detail.html", user=user, assignments=assignments)


@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if 'credentials' not in session:
        return redirect('authorize')
    user = get_user_by_id(user_id)
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        db_session = SessionLocal()

        exists = db_session.query(User).filter(
            User.email == email, User.id != user_id).first()
        if exists:
            error = "A user with this email already exists."
            db_session.close()
            return render_template("edit_user.html", user=user, error=error)
        db_session.close()
        update_user(user_id, name, email)
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("edit_user.html", user=user, error=error)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user_route(user_id):
    if 'credentials' not in session:
        return redirect('authorize')
    success = soft_delete_user(user_id)
    return redirect(url_for("index"))


@app.route("/laptops")
@login_required
def list_laptops():
    if 'credentials' not in session:
        return redirect('authorize')
    show_unassigned = request.args.get("unassigned") == "1"
    db_session = SessionLocal()
    if show_unassigned:
        # Get all laptop IDs that are currently assigned
        assigned_ids = set([a.laptop_item_id for a in db_session.query(
            LaptopAssignment).filter_by(unassigned_at=None).all()])
        laptops = db_session.query(LaptopItem).filter(~LaptopItem.id.in_(
            assigned_ids), LaptopItem.is_retired == False, LaptopItem.is_active == True).all()
    else:
        laptops = db_session.query(LaptopItem).filter(
            LaptopItem.is_retired == False, LaptopItem.is_active == True).all()
    db_session.close()
    return render_template("laptops.html", laptops=laptops, show_unassigned=show_unassigned)


@app.route("/assign", methods=["GET", "POST"])
@login_required
def assign_laptop():
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    users = db_session.query(User).all()
    # Only show laptops that are not assigned and not retired
    assigned_ids = set([a.laptop_item_id for a in db_session.query(
        LaptopAssignment).filter_by(unassigned_at=None).all()])
    laptops = db_session.query(LaptopItem).filter(~LaptopItem.id.in_(
        assigned_ids), LaptopItem.is_retired == False).all()
    db_session.close()
    error = None
    if request.method == "POST":
        user_id = int(request.form["user_id"])
        laptop_item_id = int(request.form["laptop_item_id"])
        db_session = SessionLocal()
        # Prevent double assignment
        active_assignment = db_session.query(LaptopAssignment).filter_by(
            laptop_item_id=laptop_item_id, unassigned_at=None).first()
        if active_assignment:
            error = "This laptop is already assigned. Please unassign it first."
            db_session.close()
            return render_template("assign_laptop.html", users=users, laptops=laptops, error=error)
        now = datetime.now().isoformat()
        assignment = LaptopAssignment(
            laptop_item_id=laptop_item_id,
            user_id=user_id,
            assigned_at=now,
            unassigned_at=None
        )
        db_session.add(assignment)
        db_session.commit()
        db_session.close()
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("assign_laptop.html", users=users, laptops=laptops, error=error)


@app.route("/unassign/<int:assignment_id>", methods=["POST"])
@login_required
def unassign_laptop_route(assignment_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    assignment = db_session.query(LaptopAssignment).filter_by(
        id=assignment_id).first()
    user_id = assignment.user_id if assignment else None
    if assignment and assignment.unassigned_at is None:
        assignment.unassigned_at = datetime.now().isoformat()
        db_session.commit()
    db_session.close()
    if user_id:
        return redirect(url_for("user_detail", user_id=user_id))
    return redirect(url_for("index"))


@app.route("/laptops/add", methods=["GET", "POST"])
@login_required
def add_laptop():
    if 'credentials' not in session:
        return redirect('authorize')
    error = None
    if request.method == "POST":
        db_session = SessionLocal()

        def get_field(name):
            value = request.form.get(name)
            return value if value and value.strip() != '' else None
        # Required fields validation
        model = get_field("laptop_model")
        serial = get_field("laptop_serial_number")
        quantity_raw = get_field("quantity")
        try:
            quantity = int(quantity_raw) if quantity_raw else 1
        except ValueError:
            quantity = 1
        if not model:
            error = "Model is required."
            db_session.close()
            return render_template("add_laptop.html", error=error)
        # Unique serial number validation (if provided and quantity==1)
        if serial and quantity == 1:
            exists = db_session.query(LaptopItem).filter_by(
                laptop_serial_number=serial).first()
            if exists:
                error = "A laptop with this serial number already exists."
                db_session.close()
                return render_template("add_laptop.html", error=error)
        # Warranty duration: ensure integer or None
        warranty_raw = get_field("warranty_duration")
        warranty_duration = int(
            warranty_raw) if warranty_raw is not None else None
        # Add laptops
        for i in range(quantity):
            serial_number = serial if (serial and quantity == 1) else None
            # If quantity > 1 and serial is provided, only assign to first, rest are None
            if serial and quantity > 1 and i > 0:
                serial_number = None
            laptop = LaptopItem(
                laptop_model=model,
                processor=get_field("processor"),
                ram=get_field("ram"),
                storage=get_field("storage"),
                model_color=get_field("model_color"),
                screen_size=get_field("screen_size"),
                laptop_os=get_field("laptop_os"),
                laptop_os_version=get_field("laptop_os_version"),
                laptop_serial_number=serial_number,
                warranty_duration=warranty_duration,
                laptop_price=get_field("laptop_price"),
                invoice_id=None,  # Manually added
                created_at=datetime.now().isoformat()
            )
            db_session.add(laptop)
        db_session.commit()
        db_session.close()
        return redirect(url_for("list_laptops"))
    return render_template("add_laptop.html", error=error)


@app.route("/laptops/<int:laptop_id>/edit", methods=["GET", "POST"])
@login_required
def edit_laptop(laptop_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    laptop = db_session.query(LaptopItem).filter_by(id=laptop_id).first()
    error = None
    if not laptop:
        db_session.close()
        return redirect(url_for("list_laptops"))
    if request.method == "POST":
        def get_field(name):
            value = request.form.get(name)
            return value if value and value.strip() != '' else None
        model = get_field("laptop_model")
        serial = get_field("laptop_serial_number")
        if not model or not serial:
            error = "Model and Serial Number are required."
            db_session.close()
            return render_template("edit_laptop.html", laptop=laptop, error=error)
        # Unique serial number validation (ignore self)
        exists = db_session.query(LaptopItem).filter(
            LaptopItem.laptop_serial_number == serial, LaptopItem.id != laptop_id).first()
        if exists:
            error = "A laptop with this serial number already exists."
            db_session.close()
            return render_template("edit_laptop.html", laptop=laptop, error=error)
        # Warranty duration: ensure integer or None
        warranty_raw = get_field("warranty_duration")
        warranty_duration = int(
            warranty_raw) if warranty_raw is not None else None
        laptop.laptop_model = model
        laptop.processor = get_field("processor")
        laptop.ram = get_field("ram")
        laptop.storage = get_field("storage")
        laptop.model_color = get_field("model_color")
        laptop.screen_size = get_field("screen_size")
        laptop.laptop_os = get_field("laptop_os")
        laptop.laptop_os_version = get_field("laptop_os_version")
        laptop.laptop_serial_number = serial
        laptop.warranty_duration = warranty_duration
        laptop.laptop_price = get_field("laptop_price")
        db_session.commit()
        db_session.close()
        return redirect(url_for("list_laptops"))
    db_session.close()
    return render_template("edit_laptop.html", laptop=laptop, error=error)


@app.route("/laptops/<int:laptop_id>")
@login_required
def laptop_detail(laptop_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    laptop = db_session.query(LaptopItem).options(joinedload(
        LaptopItem.maintenance_logs)).filter_by(id=laptop_id).first()
    assignments = []
    if laptop:
        assignments = db_session.query(LaptopAssignment).options(joinedload(
            LaptopAssignment.user)).filter_by(laptop_item_id=laptop_id).all()
    db_session.close()
    return render_template("laptop_detail.html", laptop=laptop, assignments=assignments)


@app.route("/laptops/<int:laptop_id>/retire", methods=["POST"])
@login_required
def retire_laptop(laptop_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    laptop = db_session.query(LaptopItem).filter_by(id=laptop_id).first()
    # Check if currently assigned
    active_assignment = db_session.query(LaptopAssignment).filter_by(
        laptop_item_id=laptop_id, unassigned_at=None).first()
    if active_assignment:
        user = db_session.query(User).filter_by(
            id=active_assignment.user_id).first()
        db_session.close()
        error = f"Cannot retire: Laptop is currently assigned to {user.name} ({user.email})"
        # Re-render the laptop detail page with error
        db_session = SessionLocal()
        laptop = db_session.query(LaptopItem).options(joinedload(
            LaptopItem.maintenance_logs)).filter_by(id=laptop_id).first()
        assignments = []
        if laptop:
            assignments = db_session.query(LaptopAssignment).options(joinedload(
                LaptopAssignment.user)).filter_by(laptop_item_id=laptop_id).all()
        db_session.close()
        return render_template("laptop_detail.html", laptop=laptop, assignments=assignments, error=error)
    if laptop:
        laptop.is_retired = True
        db_session.commit()
    db_session.close()
    return redirect(url_for("laptop_detail", laptop_id=laptop_id))


@app.route("/laptops/<int:laptop_id>/maintenance", methods=["GET", "POST"])
@login_required
def add_maintenance_log(laptop_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    laptop = db_session.query(LaptopItem).filter_by(id=laptop_id).first()
    error = None
    if not laptop:
        db_session.close()
        return redirect(url_for("list_laptops"))
    if request.method == "POST":
        description = request.form.get("description")
        performed_by = request.form.get("performed_by")
        if not description or not performed_by:
            error = "Description and Performed By are required."
            db_session.close()
            return render_template("add_maintenance.html", laptop=laptop, error=error)
        log = MaintenanceLog(
            laptop_item_id=laptop_id,
            date=datetime.now().isoformat(),
            description=description,
            performed_by=performed_by
        )
        db_session.add(log)
        db_session.commit()
        db_session.close()
        return redirect(url_for("laptop_detail", laptop_id=laptop_id))
    db_session.close()
    return render_template("add_maintenance.html", laptop=laptop, error=error)


@app.route("/replace_device/<int:assignment_id>", methods=["GET", "POST"])
@login_required
def replace_device(assignment_id):
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    assignment = db_session.query(LaptopAssignment).filter_by(
        id=assignment_id).first()
    if not assignment or assignment.unassigned_at:
        db_session.close()
        return redirect(url_for("user_detail", user_id=assignment.user_id if assignment else 1))
    user_id = assignment.user_id
    old_laptop_id = assignment.laptop_item_id
    # Get all unassigned and not retired laptops
    assigned_ids = set([a.laptop_item_id for a in db_session.query(
        LaptopAssignment).filter_by(unassigned_at=None).all()])
    unassigned_laptops = db_session.query(LaptopItem).filter(
        ~LaptopItem.id.in_(assigned_ids), LaptopItem.is_retired == False).all()
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
        db_session.add(new_assignment)
        db_session.commit()
        db_session.close()
        return redirect(url_for("user_detail", user_id=user_id))
    db_session.close()
    return render_template("replace_device.html", assignment=assignment, unassigned_laptops=unassigned_laptops, error=error)


@app.route("/download_invoices")
@login_required
def download_invoices():
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    invoices = db_session.query(LaptopInvoice).all()
    data = []
    # Add all laptops, including those not linked to an invoice
    all_laptops = db_session.query(LaptopItem).all()
    for item in all_laptops:
        invoice = item.invoice if item.invoice_id else None
        row = {
            'Invoice Number': invoice.invoice_number if invoice else '',
            'Order Date': invoice.order_date if invoice else '',
            'Invoice Date': invoice.invoice_date if invoice else '',
            'Order Number': invoice.order_number if invoice else '',
            'Supplier Name': invoice.supplier_name if invoice else '',
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
    db_session.close()

    # Ensure output/assets directory exists
    output_dir = os.path.join(os.path.dirname(
        __file__), '..', 'output', 'assets')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "laptop_invoices_download.xlsx")
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)


@app.route("/download_asset_records")
@login_required
def download_asset_records():
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    laptops = db_session.query(LaptopItem).all()
    data = []
    for laptop in laptops:
        # Find active assignment
        active_assignment = (
            db_session.query(LaptopAssignment)
            .filter_by(laptop_item_id=laptop.id, unassigned_at=None)
            .first()
        )
        assigned_to = None
        assigned_to_email = None
        if active_assignment:
            user = db_session.query(User).filter_by(
                id=active_assignment.user_id).first()
            if user:
                assigned_to = user.name
                assigned_to_email = user.email
        row = {
            'Laptop ID': laptop.id,
            'Model': laptop.laptop_model,
            'Serial Number': laptop.laptop_serial_number,
            'Status': 'Retired/Disposed' if laptop.is_retired else 'Active',
            'Is Retired': laptop.is_retired,
            'Assigned': True if assigned_to else False,
            'Assigned To': assigned_to or '',
            'Assigned To Email': assigned_to_email or '',
            'Created At': laptop.created_at,
            'Warranty Expiry': laptop.warranty_expiry,
            'Price': laptop.laptop_price
        }
        data.append(row)
    db_session.close()
    output_dir = os.path.join(os.path.dirname(
        __file__), '..', 'output', 'assets')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "asset_records_download.csv")
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)


@app.route("/download_assignment_history")
@login_required
def download_assignment_history():
    if 'credentials' not in session:
        return redirect('authorize')
    db_session = SessionLocal()
    assignments = db_session.query(LaptopAssignment).all()
    data = []
    for assignment in assignments:
        laptop = db_session.query(LaptopItem).filter_by(
            id=assignment.laptop_item_id).first()
        user = db_session.query(User).filter_by(id=assignment.user_id).first()
        row = {
            'Assignment ID': assignment.id,
            'Laptop ID': assignment.laptop_item_id,
            'Laptop Model': laptop.laptop_model if laptop else '',
            'Laptop Serial Number': laptop.laptop_serial_number if laptop else '',
            'User ID': assignment.user_id,
            'User Name': user.name if user else '',
            'User Email': user.email if user else '',
            'Assigned At': assignment.assigned_at,
            'Unassigned At': assignment.unassigned_at or '',
        }
        data.append(row)
    db_session.close()
    output_dir = os.path.join(os.path.dirname(
        __file__), '..', 'output', 'assets')
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "assignment_history_download.csv")
    df = pd.DataFrame(data).sort_values(by="Laptop ID")
    df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)


def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }


def get_drive_tree(service, parent_id='root'):
    """
    Recursively builds a tree of files/folders from Google Drive.
    Returns a nested dict structure.
    """
    query = f"'{parent_id}' in parents and trashed = false"
    results = service.files().list(
        q=query, fields="files(id, name, mimeType)", pageSize=1000).execute()
    items = results.get('files', [])
    tree = []
    for item in items:
        node = {
            'id': item['id'],
            'name': item['name'],
            'mimeType': item['mimeType']
        }
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            node['children'] = get_drive_tree(service, item['id'])
        tree.append(node)
    return tree


@app.route('/drive_tree_children/<folder_id>')
@login_required
def drive_tree_children(folder_id):
    if 'credentials' not in session:
        return ''
    creds = Credentials.from_authorized_user_info(session['credentials'])
    service = build('drive', 'v3', credentials=creds)
    children = get_drive_tree(service, folder_id)

    def render_tree(nodes, parent_path=""):
        html = '<ul style="margin-left:20px">'
        for node in nodes:
            if node['mimeType'] == 'application/vnd.google-apps.folder':
                folder_path = f"{parent_path}/{node['name']}" if parent_path else node['name']
                html += f'<li class="folder"><span class="toggle">+</span> <span class="folder-name">📁 {node["name"]}</span> <button class="select-folder-btn" data-folder-path="{folder_path}">Select Folder</button><div class="children" style="display:none" data-folder-id="{node["id"]}" data-folder-path="{folder_path}"></div></li>'
            else:
                html += f'<li class="file">📄 {node["name"]}</li>'
        html += '</ul>'
        return html
    parent_path = request.args.get('parent_path', '')
    return render_tree(children, parent_path)


@app.route('/drive_tree')
@login_required
def drive_tree():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

    creds = Credentials.from_authorized_user_info(session['credentials'])
    service = build('drive', 'v3', credentials=creds)
    tree = get_drive_tree(service)

    def render_tree(nodes, parent_path=""):
        html = '<ul>'
        for node in nodes:
            if node['mimeType'] == 'application/vnd.google-apps.folder':
                folder_path = f"{parent_path}/{node['name']}" if parent_path else node['name']
                html += f'''
                    <li class="folder">
                        <span class="toggle">+</span>
                        <span class="folder-name">📁 {node["name"]}</span>
                        <button class="select-folder-btn" data-folder-path="{folder_path}">Select Folder</button>
                        <div class="children" style="display:none" data-folder-id="{node["id"]}" data-folder-path="{folder_path}"></div>
                    </li>
                '''
            else:
                html += f'<li class="file">📄 {node["name"]}</li>'
        html += '</ul>'
        return html

    tree_html = render_tree(tree)
    return render_template("drive_tree.html", tree_html=tree_html)


def list_all_files_in_folder(service, folder_id):
    """
    Recursively list all files in a Google Drive folder by folder_id.
    Returns a list of dicts: [{id, name, modifiedTime}]
    """
    files = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageToken=page_token
        ).execute()
        for file in response.get('files', []):
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                files.extend(list_all_files_in_folder(service, file['id']))
            else:
                files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'mimeType': file['mimeType'],
                    'modifiedTime': file.get('modifiedTime', '')
                })
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break
    return files


def render_files_table(files):
    if not files:
        return '<p>No files found in this folder.</p>'
    html = '<table border="1" id="drive-files-table"><tr><th>Filename</th><th>Last Edited</th></tr>'
    for f in files:
        html += f'<tr><td>{f["name"]}</td><td>{f["modifiedTime"]}</td></tr>'
    html += '</table>'
    return html


@app.route('/confirm_folder', methods=['POST'])
def confirm_folder():
    if 'credentials' not in session:
        return '<p>Not authorized.</p>', 401
    creds = Credentials.from_authorized_user_info(session['credentials'])
    service = build('drive', 'v3', credentials=creds)
    data = request.get_json()
    folder_id = data.get('folder_id')
    if not folder_id:
        return '<p>No folder selected.</p>', 400
    # ensure_drive_files_table() # Removed call to old SQLite function
    files = list_all_files_in_folder(service, folder_id)
    try:
        upsert_drive_files_sqlalchemy(files)  # Use the new SQLAlchemy function
    except Exception as e:
        # Log the error e.g., app.logger.error(f"Error upserting drive files: {e}")
        return f"<p>Error updating database: {e}</p>", 500
    return render_files_table(files)


@app.route('/extract_text_from_drive_folder')
def extract_text_from_drive_folder():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

    folder_id = request.args.get('folder_id')
    if not folder_id:
        return "Please provide a 'folder_id' query parameter.", 400

    creds = Credentials.from_authorized_user_info(session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    try:
        # Check if the folder_id is valid by trying to get its metadata
        folder_metadata = service.files().get(
            fileId=folder_id, fields="id, name, mimeType").execute()
        if folder_metadata.get('mimeType') != 'application/vnd.google-apps.folder':
            return f"The provided ID '{folder_id}' is not a folder.", 400
        print(
            f"Accessing folder: {folder_metadata.get('name')} (ID: {folder_id})")
    except Exception as e:
        return f"Invalid folder_id or error accessing folder: {e}", 400

    all_files_in_folder = list_all_files_in_folder(service, folder_id)
    pdf_files_found = False
    extracted_texts_summary = []

    print(f"\nStarting PDF text extraction for folder ID: {folder_id}")
    # 1. Get current DB state for drive files
    db_files = get_all_drive_files()  # {name: (last_edited, id)}
    # 2. Build a set of current drive file names and ids from the folder
    current_drive_file_names = set()
    current_drive_file_ids = set()
    for file_item in all_files_in_folder:
        if file_item.get('mimeType') == 'application/pdf':
            current_drive_file_names.add(file_item['name'])
            current_drive_file_ids.add(file_item['id'])
    # 3. Find files in DB that are no longer in Drive and delete their PO data (by filename)
    db_file_names = set(db_files.keys())
    for db_name, (db_last_edited, db_id) in db_files.items():
        if db_name not in current_drive_file_names:
            print(
                f"File '{db_name}' (id={db_id}) deleted from Drive (by filename). Removing from database...")
            delete_po_by_drive_file_id(db_id)
    # 4. For each file in Drive, decide to skip, update, or add
    for file_item in all_files_in_folder:
        if file_item.get('mimeType') != 'application/pdf':
            continue
        file_name = file_item['name']
        file_id = file_item['id']
        file_last_edited = file_item.get('modifiedTime')
        # Convert modifiedTime to datetime for comparison
        from datetime import datetime
        file_last_edited_dt = None
        if file_last_edited:
            try:
                if file_last_edited.endswith('Z'):
                    file_last_edited_dt = datetime.fromisoformat(
                        file_last_edited[:-1] + '+00:00')
                else:
                    file_last_edited_dt = datetime.fromisoformat(
                        file_last_edited)
            except Exception:
                pass
        db_entry = db_files.get(file_name)
        if db_entry:
            db_last_edited, db_id = db_entry
            if db_last_edited == file_last_edited_dt:
                print(f"Skipping {file_name} (unchanged)")
                continue  # Skip unchanged
            else:
                print(f"Updating {file_name} (timestamp changed)")
                # Remove old PO data for this file id before reprocessing
                delete_po_by_drive_file_id(file_id)
        else:
            print(f"Adding new file {file_name}")
        try:
            # Download the file
            request_file = service.files().get_media(fileId=file_item['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request_file)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            # --- Integration of extract_blocks and extract_tables ---
            temp_pdf_path = None
            try:
                # Create a temporary file to save the PDF content
                temp_dir = tempfile.gettempdir()
                # Generate a unique filename to avoid conflicts if multiple requests happen concurrently
                temp_pdf_filename = f"temp_drive_pdf_{file_item['id']}_{os.urandom(4).hex()}.pdf"
                temp_pdf_path = os.path.join(temp_dir, temp_pdf_filename)

                with open(temp_pdf_path, 'wb') as f_temp:
                    f_temp.write(fh.getvalue())

                print(
                    f"  PDF content for {file_item['name']} saved to temporary file: {temp_pdf_path}")

                # --- RUN EXTRACTION PIPELINE (like main.py) ---
                print(
                    f"  Running extraction pipeline for {file_item['name']}...")
                po_json_data_for_db = run_pipeline(temp_pdf_path)
                if po_json_data_for_db:
                    insert_or_replace_po(po_json_data_for_db)
                    print(
                        f"  Successfully inserted/replaced PO data for {file_item['name']} into database.")
                    extracted_texts_summary.append(
                        f"Inserted/replaced PO data for: {file_item['name']}")
                else:
                    print(
                        f"  Warning: No data extracted from {file_item['name']}. Skipping database insertion for this file.")
                    extracted_texts_summary.append(
                        f"No data extracted from {file_item['name']}. DB insert skipped.")
                # --- END PIPELINE ---

            finally:
                # Clean up the temporary file
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    print(f"  Deleting temporary file: {temp_pdf_path}")
                    os.remove(temp_pdf_path)

        except Exception as error:
            error_message = f"Error processing file {file_item['name']} (ID: {file_item['id']}): {error}"
            print(f"{error_message}\n{'-'*80}")
            extracted_texts_summary.append(
                f"Error processing: {file_item['name']} - {error}")
        finally:
            if fh:
                fh.close()
        pdf_files_found = True

    print(f"Finished processing folder ID: {folder_id}\n")

    # --- Export and Forecast steps (like main.py) ---
    print("\n--- Exporting Data to JSON and CSV ---")
    from extractor.export import export_all_pos_json, export_all_csvs
    export_all_pos_json()
    export_all_csvs()
    print("--- Data Export Complete ---")

    print("\n--- Generating Financial Forecast ---")
    from forecast_processor import run_forecast_processing
    run_forecast_processing(input_json_path="./output/purchase_orders.json")
    print("--- Financial Forecast Generation Complete ---")

    print("\nAll processes finished successfully!")

    if not pdf_files_found:
        message = f"No PDF files found in the specified folder '{folder_metadata.get('name')}' (ID: {folder_id})."
        print(message)
        return message
    else:
        response_message = f"PDF text extraction process initiated for folder '{folder_metadata.get('name')}' (ID: {folder_id}). Check your terminal for output. Summary of processed files:<br>"
        response_message += "<br>".join(extracted_texts_summary)
        return response_message


if __name__ == "__main__":
    app.run(port=8000, debug=True)
