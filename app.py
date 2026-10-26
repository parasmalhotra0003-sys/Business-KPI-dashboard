from flask import Flask, render_template, redirect, url_for, session
from config import Config
from database.connection import init_db_pool
from routes.auth import auth_bp, login_required

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database connection pool
try:
    init_db_pool(Config)
except Exception as e:
    print(f"CRITICAL: Failed to initialize database: {e}")

# Register Blueprints
app.register_blueprint(auth_bp)

# Temporary/skeleton placeholders for other blueprints will be registered here
from routes.dashboard import dashboard_bp
from routes.customers import customers_bp
from routes.products import products_bp
from routes.sales import sales_bp
from routes.expenses import expenses_bp
from routes.reports import reports_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(products_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(reports_bp)

@app.route('/')
@login_required
def dashboard_view():
    """
    Main landing route serving the dashboard page (only for logged-in users).
    """
    return render_template('dashboard.html', username=session.get('username'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
