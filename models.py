"""SQL and business rules. app.py calls these functions; it never contains
SQL itself, and nothing in here knows about HTML."""
import math
from datetime import date
from decimal import Decimal, InvalidOperation

import pymysql

from db import execute, get_db, query_all, query_one


# =====================================================================
# Products
# =====================================================================
def stock_status(stock, reorder_level):
    """Return (label, badge colour class) calculated from the numbers."""
    if stock == 0:
        return "Out of stock", "danger"
    if stock <= reorder_level:
        return "Restock", "danger"
    if stock <= reorder_level * 2:
        return "Low stock", "warning"
    return "In stock", "success"


def _add_status(rows):
    for row in rows:
        row["status"], row["badge"] = stock_status(row["stock"], row["reorder_level"])
    return rows


PRODUCT_SELECT = """
    SELECT p.id, p.name, p.category_id, c.name AS category,
           p.stock, p.reorder_level, p.price
    FROM products p
    JOIN categories c ON c.id = p.category_id
"""


def list_products(search="", category_id=None):
    sql = PRODUCT_SELECT + " WHERE 1=1"
    params = []
    if search:
        sql += " AND p.name LIKE %s"
        params.append(f"%{search}%")
    if category_id:
        sql += " AND p.category_id = %s"
        params.append(category_id)
    sql += " ORDER BY p.name"
    return _add_status(query_all(sql, params))


def get_product(product_id):
    row = query_one(PRODUCT_SELECT + " WHERE p.id = %s", (product_id,))
    return _add_status([row])[0] if row else None


def list_categories():
    return query_all("SELECT id, name FROM categories ORDER BY name")


def validate_product(form):
    """Check a submitted product form. Returns (clean values, list of errors)."""
    errors = []

    name = form.get("name", "").strip()
    if not name:
        errors.append("Product name is required.")
    elif len(name) > 120:
        errors.append("Product name must be 120 characters or fewer.")

    category_id = None
    try:
        category_id = int(form.get("category_id", ""))
        if not query_one("SELECT id FROM categories WHERE id = %s", (category_id,)):
            errors.append("Choose a valid category.")
    except ValueError:
        errors.append("Choose a category.")

    def whole_number(field, label):
        try:
            value = int(form.get(field, ""))
            if value < 0:
                errors.append(f"{label} cannot be negative.")
            return value
        except ValueError:
            errors.append(f"{label} must be a whole number.")
            return None

    stock = whole_number("stock", "Stock")
    reorder_level = whole_number("reorder_level", "Reorder level")

    price = None
    try:
        price = Decimal(form.get("price", "").strip())
        if not price.is_finite() or price < 0:
            errors.append("Price must be zero or more.")
        elif price >= Decimal("100000000"):
            errors.append("Price is too large.")
        else:
            price = price.quantize(Decimal("0.01"))
    except InvalidOperation:
        errors.append("Price must be a number, e.g. 9.50.")

    return dict(name=name, category_id=category_id, stock=stock,
                reorder_level=reorder_level, price=price), errors


def create_product(name, category_id, stock, reorder_level, price):
    return execute(
        "INSERT INTO products (name, category_id, stock, reorder_level, price) "
        "VALUES (%s, %s, %s, %s, %s)",
        (name, category_id, stock, reorder_level, price),
    )


def update_product(product_id, name, category_id, stock, reorder_level, price):
    execute(
        "UPDATE products SET name = %s, category_id = %s, stock = %s, "
        "reorder_level = %s, price = %s WHERE id = %s",
        (name, category_id, stock, reorder_level, price, product_id),
    )


def delete_product(product_id):
    """False when the database refuses (the product already has orders)."""
    try:
        execute("DELETE FROM products WHERE id = %s", (product_id,))
        return True
    except pymysql.err.IntegrityError:
        get_db().rollback()
        return False


# =====================================================================
# Clients
# =====================================================================
def list_clients():
    # LEFT JOIN keeps clients who have no orders yet
    return query_all("""
        SELECT c.id, c.name, c.email, c.company, c.active,
               COUNT(o.id) AS order_count,
               COALESCE(SUM(o.quantity * o.unit_price), 0) AS total_spent
        FROM clients c
        LEFT JOIN orders o ON o.client_id = c.id
        GROUP BY c.id, c.name, c.email, c.company, c.active
        ORDER BY c.name
    """)


def create_client(name, email, company):
    try:
        execute(
            "INSERT INTO clients (name, email, company) VALUES (%s, %s, %s)",
            (name, email, company or None),
        )
        return True, f"Client '{name}' added."
    except pymysql.err.IntegrityError:
        get_db().rollback()
        return False, "A client with that email already exists."


def toggle_client(client_id):
    execute("UPDATE clients SET active = 1 - active WHERE id = %s", (client_id,))


def get_client(client_id):
    return query_one("SELECT id, name, active FROM clients WHERE id = %s", (client_id,))


# =====================================================================
# Orders
# =====================================================================
def list_orders(limit=50):
    return query_all("""
        SELECT o.id, o.ordered_at, o.quantity, o.unit_price,
               o.quantity * o.unit_price AS total,
               c.name AS client, p.name AS product
        FROM orders o
        JOIN clients  c ON c.id = o.client_id
        JOIN products p ON p.id = o.product_id
        ORDER BY o.ordered_at DESC, o.id DESC
        LIMIT %s
    """, (limit,))


def place_order(client_id, product_id, quantity):
    """Save the order AND reduce the stock in one transaction: both or neither."""
    if quantity <= 0:
        return False, "Quantity must be at least 1."

    db = get_db()
    try:
        with db.cursor() as cur:
            # FOR UPDATE locks this product row until we commit or roll back,
            # so two simultaneous orders cannot both take the last unit.
            cur.execute("SELECT name, stock, price FROM products "
                        "WHERE id = %s FOR UPDATE", (product_id,))
            product = cur.fetchone()
            if product is None:
                db.rollback()
                return False, "That product does not exist."

            cur.execute("SELECT name, active FROM clients WHERE id = %s", (client_id,))
            client = cur.fetchone()
            if client is None or not client["active"]:
                db.rollback()
                return False, "That client does not exist or is inactive."

            if quantity > product["stock"]:
                db.rollback()
                return False, (f"Not enough stock: only {product['stock']} x "
                               f"{product['name']} available.")

            cur.execute("INSERT INTO orders (client_id, product_id, quantity, unit_price) "
                        "VALUES (%s, %s, %s, %s)",
                        (client_id, product_id, quantity, product["price"]))
            cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s",
                        (quantity, product_id))

        db.commit()  # both changes saved together
        return True, f"Order placed: {quantity} x {product['name']} for {client['name']}."
    except Exception:
        db.rollback()  # undo BOTH
        raise


# =====================================================================
# Dashboard
# =====================================================================
def dashboard_stats():
    revenue = query_one("""
        SELECT COALESCE(SUM(quantity * unit_price), 0) AS v
        FROM orders WHERE ordered_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)["v"]
    previous = query_one("""
        SELECT COALESCE(SUM(quantity * unit_price), 0) AS v
        FROM orders
        WHERE ordered_at >= DATE_SUB(NOW(), INTERVAL 60 DAY)
          AND ordered_at <  DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)["v"]
    revenue, previous = float(revenue), float(previous)
    growth = ((revenue - previous) / previous * 100) if previous else None

    active_clients = query_one(
        "SELECT COUNT(*) AS n FROM clients WHERE active = 1")["n"]
    buying = query_one("""
        SELECT COUNT(DISTINCT o.client_id) AS n
        FROM orders o JOIN clients c ON c.id = o.client_id
        WHERE c.active = 1 AND o.ordered_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)["n"]
    conversion = (buying / active_clients) if active_clients else 0

    orders_30 = query_one("""
        SELECT COUNT(*) AS n FROM orders
        WHERE ordered_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)["n"]

    products = list_products()
    restock = [p for p in products if p["badge"] == "danger"]

    return dict(revenue=revenue, previous_revenue=previous, growth=growth,
                active_clients=active_clients, buying_clients=buying,
                conversion_rate=conversion, orders_30=orders_30,
                products=products, restock=restock,
                product_count=len(products))


def monthly_revenue(months=6):
    """Revenue per month for the last `months` months, oldest first."""
    rows = query_all("""
        SELECT DATE_FORMAT(ordered_at, '%%Y-%%m') AS ym,
               SUM(quantity * unit_price) AS revenue
        FROM orders
        WHERE ordered_at >= DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-01'), INTERVAL %s MONTH)
        GROUP BY ym
    """, (months - 1,))
    by_month = {r["ym"]: float(r["revenue"]) for r in rows}

    # Fill in months with no sales as 0
    today = date.today()
    out = []
    for back in range(months - 1, -1, -1):
        y, m = divmod(today.year * 12 + today.month - 1 - back, 12)
        d = date(y, m + 1, 1)
        ym = d.strftime("%Y-%m")
        out.append(dict(ym=ym, label=d.strftime("%b"), revenue=by_month.get(ym, 0.0)))

    top = max((m["revenue"] for m in out), default=0) or 1
    for m in out:
        m["height"] = max(8, round(m["revenue"] / top * 100)) if m["revenue"] else 8
    return out


# =====================================================================
# Reports: ABC classification and EOQ
# =====================================================================
def product_sales(days=365):
    """Units sold and revenue per product over the last `days` days."""
    return query_all("""
        SELECT p.id, p.name, p.price, p.stock,
               COALESCE(SUM(o.quantity), 0) AS units,
               COALESCE(SUM(o.quantity * o.unit_price), 0) AS revenue
        FROM products p
        LEFT JOIN orders o
               ON o.product_id = p.id
              AND o.ordered_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY p.id, p.name, p.price, p.stock
    """, (days,))


def classify_abc(items):
    """A = first 80% of value, B = next 15%, C = the rest."""
    items = sorted(items, key=lambda i: i["value"], reverse=True)
    total = sum(i["value"] for i in items)
    running = 0
    for item in items:
        running += item["value"]
        pct = running / total if total else 1
        item["share"] = item["value"] / total * 100 if total else 0
        item["cumulative"] = pct * 100
        item["tier"] = "A" if pct <= 0.8 else ("B" if pct <= 0.95 else "C")
    if items:
        items[0]["tier"] = "A"  # the top product is always A
    return items


def abc_report():
    items = [dict(name=r["name"], units=int(r["units"]), value=float(r["revenue"]))
             for r in product_sales()]
    return classify_abc(items)


def calculate_eoq(demand, ordering_cost, holding_cost):
    if holding_cost <= 0:
        return None
    return math.sqrt((2 * demand * ordering_cost) / holding_cost)


def eoq_report(ordering_cost, holding_rate):
    rows = []
    for r in product_sales():
        demand = int(r["units"])
        if demand == 0:
            continue
        holding = float(r["price"]) * holding_rate
        eoq = calculate_eoq(demand, ordering_cost, holding)
        rows.append(dict(name=r["name"], demand=demand, stock=r["stock"],
                         holding=holding,
                         eoq=round(eoq) if eoq is not None else None))
    return sorted(rows, key=lambda r: r["name"])
