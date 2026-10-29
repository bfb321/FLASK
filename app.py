import os
import re

import pymysql
from flask import (Flask, flash, redirect, render_template, request,
                   url_for)
from werkzeug.security import generate_password_hash

import db
import models

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")  # needed for flash()
db.init_app(app)


# ---------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------
@app.route("/")
def index():
    stats = models.dashboard_stats()
    return render_template("index.html", stats=stats,
                           months=models.monthly_revenue(6))


# ---------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------
@app.route("/products")
def products():
    search = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)
    return render_template("products.html",
                           products=models.list_products(search, category_id),
                           categories=models.list_categories(),
                           search=search, category_id=category_id)


@app.route("/products/new", methods=["GET", "POST"])
def product_new():
    if request.method == "POST":
        values, errors = models.validate_product(request.form)
        if not errors:
            models.create_product(**values)
            flash(f"Product '{values['name']}' added.", "success")
            return redirect(url_for("products"))
        for e in errors:
            flash(e, "error")
        return render_template("product_form.html", product=request.form,
                               categories=models.list_categories(), editing=False)
    return render_template("product_form.html",
                           product={"reorder_level": 10, "stock": 0},
                           categories=models.list_categories(), editing=False)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    product = models.get_product(product_id)
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        values, errors = models.validate_product(request.form)
        if not errors:
            models.update_product(product_id, **values)
            flash(f"Product '{values['name']}' updated.", "success")
            return redirect(url_for("products"))
        for e in errors:
            flash(e, "error")
        product = request.form

    return render_template("product_form.html", product=product, product_id=product_id,
                           categories=models.list_categories(), editing=True)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    product = models.get_product(product_id)
    if product is None:
        flash("Product not found.", "error")
    elif models.delete_product(product_id):
        flash(f"Product '{product['name']}' deleted.", "success")
    else:
        flash(f"'{product['name']}' has orders, so it cannot be deleted.", "error")
    return redirect(url_for("products"))


# ---------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------
@app.route("/clients", methods=["GET", "POST"])
def clients():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        company = request.form.get("company", "").strip()
        if not name or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a name and a valid email address.", "error")
        elif len(name) > 120 or len(email) > 160 or len(company) > 160:
            flash("One of the fields is too long.", "error")
        else:
            ok, message = models.create_client(name, email, company)
            flash(message, "success" if ok else "error")
        return redirect(url_for("clients"))
    return render_template("clients.html", clients=models.list_clients())


@app.route("/clients/<int:client_id>/toggle", methods=["POST"])
def client_toggle(client_id):
    client = models.get_client(client_id)
    if client is None:
        flash("Client not found.", "error")
    else:
        models.toggle_client(client_id)
        state = "deactivated" if client["active"] else "activated"
        flash(f"Client '{client['name']}' {state}.", "success")
    return redirect(url_for("clients"))


@app.route("/client")
def client():
    # The old /client link from earlier classes now goes to the clients page
    return redirect(url_for("clients"))


# ---------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------
@app.route("/orders", methods=["GET", "POST"])
def orders():
    if request.method == "POST":
        try:
            client_id = int(request.form.get("client_id", ""))
            product_id = int(request.form.get("product_id", ""))
            quantity = int(request.form.get("quantity", ""))
        except ValueError:
            flash("Choose a client, a product and enter a whole-number quantity.", "error")
            return redirect(url_for("orders"))
        ok, message = models.place_order(client_id, product_id, quantity)
        flash(message, "success" if ok else "error")
        return redirect(url_for("orders"))

    active_clients = [c for c in models.list_clients() if c["active"]]
    return render_template("orders.html",
                           orders=models.list_orders(),
                           clients=active_clients, products=models.list_products())


# ---------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------
@app.route("/reports")
def reports():
    ordering_cost = request.args.get("ordering_cost", 50, type=float)
    holding_pct = request.args.get("holding_pct", 20, type=float)
    if ordering_cost < 0:
        flash("Ordering cost cannot be negative - using 50.", "error")
        ordering_cost = 50
    if holding_pct <= 0:
        flash("Holding cost % must be above 0 - using 20%.", "error")
        holding_pct = 20
    return render_template("reports.html",
                           abc=models.abc_report(),
                           eoq=models.eoq_report(ordering_cost, holding_pct / 100),
                           ordering_cost=ordering_cost,
                           holding_pct=holding_pct)


# ---------------------------------------------------------------------
# Registered users (registration exercise)
# ---------------------------------------------------------------------
@app.route("/users")
def users():
    # password_hash is deliberately not selected
    all_users = db.query_all(
        """SELECT user_id, first_name, last_name, business_name, email, phone, address, created_at
           FROM users
           ORDER BY user_id"""
    )
    return render_template("users.html", users=all_users)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", form={})

    form = {k: request.form.get(k, "").strip()
            for k in ("firstName", "lastName", "businessName", "email", "phone", "address")}
    password = request.form.get("password", "")
    confirm = request.form.get("confirmPassword", "")

    errors = []
    if not all(form.values()):
        errors.append("All fields are required.")
    if form["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", form["email"]):
        errors.append("Enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")

    if not errors:
        try:
            db.execute(
                """INSERT INTO users (first_name, last_name, business_name, email, phone, address, password_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (form["firstName"], form["lastName"], form["businessName"],
                 form["email"].lower(), form["phone"], form["address"],
                 generate_password_hash(password)),
            )
            flash(f"Account created for {form['businessName']}.", "success")
            return redirect(url_for("users"))
        except pymysql.err.IntegrityError:
            db.get_db().rollback()
            errors.append("An account with that email already exists.")

    for error in errors:
        flash(error, "error")
    return render_template("register.html", form=form), 400


if __name__ == "__main__":
    app.run(debug=True)
