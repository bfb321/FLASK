from flask import Flask, render_template
app = Flask(__name__)
products = [
    {"name": "BFB321", "category": "Electronics", "stock": 84, "price": 1250, "status": "In stock"},
    {"name": "Office Chair", "category": "Furniture", "stock": 26, "price": 320, "status": "Low stock"},
    {"name": "Wireless Mouse", "category": "Accessories", "stock": 200, "price": 42, "status": "In stock"},
    {"name": "Monitor 27", "category": "Electronics", "stock": 12, "price": 610, "status": "Restock"},
]
@app.route('/')
def home():
    revenue = 1000.2 # this come from database
    active_users = 200000 # this come from database
    conversion_rate = 0.05 # this come from database
    return render_template('index.html', revenue=revenue, active_users=active_users, conversion_rate=conversion_rate, products=products)
@app.route('/contact')
def contact():
    return render_template('contact.html')
@app.route('/project')
def project():
    return render_template('project.html')
@app.route('/client')
def client():
    return render_template('client.html')
if __name__=='__main__':
    app.run(debug=True)
