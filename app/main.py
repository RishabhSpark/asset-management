import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for
from db.crud import create_user, get_all_users, get_user_by_id, update_user, delete_user, assign_laptop_to_user, get_assignments_for_user, get_assignments_for_laptop, unassign_laptop
from db.database import SessionLocal, LaptopItem, LaptopAssignment, User
from sqlalchemy.orm import joinedload

app = Flask(__name__)

@app.route("/")
def index():
    users = get_all_users()
    return render_template("index.html", users=users)

@app.route("/users/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        create_user(name, email)
        return redirect(url_for("index"))
    return render_template("add_user.html")

@app.route("/users/<int:user_id>")
def user_detail(user_id):
    user = get_user_by_id(user_id)
    assignments = get_assignments_for_user(user_id)
    return render_template("user_detail.html", user=user, assignments=assignments)

@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    user = get_user_by_id(user_id)
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        update_user(user_id, name, email)
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("edit_user.html", user=user)

@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user_route(user_id):
    delete_user(user_id)
    return redirect(url_for("index"))

@app.route("/laptops")
def list_laptops():
    session = SessionLocal()
    laptops = session.query(LaptopItem).all()
    session.close()
    return render_template("laptops.html", laptops=laptops)

@app.route("/assign", methods=["GET", "POST"])
def assign_laptop():
    session = SessionLocal()
    users = session.query(User).all()
    laptops = session.query(LaptopItem).all()
    session.close()
    if request.method == "POST":
        user_id = int(request.form["user_id"])
        laptop_item_id = int(request.form["laptop_item_id"])
        # Always create a new assignment record (do not delete old ones)
        from db.database import LaptopAssignment
        from datetime import datetime
        session = SessionLocal()
        assignment = LaptopAssignment(
            laptop_item_id=laptop_item_id,
            user_id=user_id,
            assigned_at=datetime.now().isoformat()
        )
        session.add(assignment)
        session.commit()
        session.close()
        return redirect(url_for("user_detail", user_id=user_id))
    return render_template("assign_laptop.html", users=users, laptops=laptops)

@app.route("/unassign/<int:assignment_id>", methods=["POST"])
def unassign_laptop_route(assignment_id):
    # Find user_id for redirect
    session = SessionLocal()
    assignment = session.query(LaptopAssignment).filter_by(id=assignment_id).first()
    user_id = assignment.user_id if assignment else None
    session.close()
    unassign_laptop(assignment_id)
    if user_id:
        return redirect(url_for("user_detail", user_id=user_id))
    return redirect(url_for("index"))

@app.route("/laptops/add", methods=["GET", "POST"])
def add_laptop():
    if request.method == "POST":
        session = SessionLocal()
        laptop = LaptopItem(
            laptop_model=request.form["laptop_model"],
            processor=request.form["processor"],
            ram=request.form["ram"],
            storage=request.form["storage"],
            model_color=request.form["model_color"],
            screen_size=request.form["screen_size"],
            laptop_os=request.form["laptop_os"],
            laptop_os_version=request.form["laptop_os_version"],
            laptop_serial_number=request.form["laptop_serial_number"],
            warranty_duration=request.form.get("warranty_duration"),
            laptop_price=request.form.get("laptop_price"),
            quantity=request.form.get("quantity", 1),
            invoice_id=None  # Or set to a valid invoice if needed
        )
        session.add(laptop)
        session.commit()
        session.close()
        return redirect(url_for("list_laptops"))
    return render_template("add_laptop.html")

@app.route("/laptops/<int:laptop_id>/edit", methods=["GET", "POST"])
def edit_laptop(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    if not laptop:
        session.close()
        return redirect(url_for("list_laptops"))
    if request.method == "POST":
        laptop.laptop_model = request.form["laptop_model"]
        laptop.processor = request.form["processor"]
        laptop.ram = request.form["ram"]
        laptop.storage = request.form["storage"]
        laptop.model_color = request.form["model_color"]
        laptop.screen_size = request.form["screen_size"]
        laptop.laptop_os = request.form["laptop_os"]
        laptop.laptop_os_version = request.form["laptop_os_version"]
        laptop.laptop_serial_number = request.form["laptop_serial_number"]
        laptop.warranty_duration = request.form.get("warranty_duration")
        laptop.laptop_price = request.form.get("laptop_price")
        laptop.quantity = request.form.get("quantity", 1)
        session.commit()
        session.close()
        return redirect(url_for("list_laptops"))
    session.close()
    return render_template("edit_laptop.html", laptop=laptop)

@app.route("/laptops/<int:laptop_id>/delete", methods=["POST"])
def delete_laptop(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    if laptop:
        session.delete(laptop)
        session.commit()
    session.close()
    return redirect(url_for("list_laptops"))

@app.route("/laptops/<int:laptop_id>")
def laptop_detail(laptop_id):
    session = SessionLocal()
    laptop = session.query(LaptopItem).filter_by(id=laptop_id).first()
    assignments = []
    if laptop:
        assignments = session.query(LaptopAssignment).options(joinedload(LaptopAssignment.user)).filter_by(laptop_item_id=laptop_id).all()
    session.close()
    return render_template("laptop_detail.html", laptop=laptop, assignments=assignments)

if __name__ == "__main__":
    app.run(debug=True)
