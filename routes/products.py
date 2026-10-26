from flask import Blueprint, request, jsonify
from routes.auth import login_required
from database.connection import execute_query, execute_update

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    try:
        search = request.args.get('search', '').strip()
        if search:
            query = """SELECT p.id, p.name, p.category, p.price, p.stock, 
                              COALESCE(SUM(s.total_amount), 0) as total_rev
                       FROM products p
                       LEFT JOIN sales s ON p.id = s.product_id AND s.status = 'Completed'
                       WHERE p.name LIKE %s OR p.category LIKE %s
                       GROUP BY p.id
                       ORDER BY p.id DESC"""
            term = f"%{search}%"
            rows = execute_query(query, (term, term))
        else:
            query = """SELECT p.id, p.name, p.category, p.price, p.stock, 
                              COALESCE(SUM(s.total_amount), 0) as total_rev
                       FROM products p
                       LEFT JOIN sales s ON p.id = s.product_id AND s.status = 'Completed'
                       GROUP BY p.id
                       ORDER BY p.id DESC"""
            rows = execute_query(query)
            
        # Format matching the client D.products template:
        # ['PR-001','Wireless Headphones','Electronics','€125','320','€12,450']
        formatted_rows = []
        for r in rows:
            formatted_rows.append([
                f"PR-{r['id']:03d}",
                r['name'],
                r['category'],
                f"${r['price']:.2f}",
                str(r['stock']),
                f"${r['total_rev']:.2f}"
            ])
            
        return jsonify({'success': True, 'data': formatted_rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price')
    stock = data.get('stock')
    
    if not name or not category or price is None or stock is None:
        return jsonify({'success': False, 'error': 'Name, Category, Price and Stock are required.'}), 400
        
    try:
        query = "INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)"
        execute_update(query, (name, category, float(price), int(stock)))
        return jsonify({'success': True, 'message': 'Product added successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/api/products/<int:pid>', methods=['PUT'])
@login_required
def update_product(pid):
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price')
    stock = data.get('stock')
    
    if not name or not category or price is None or stock is None:
        return jsonify({'success': False, 'error': 'Name, Category, Price and Stock are required.'}), 400
        
    try:
        query = "UPDATE products SET name = %s, category = %s, price = %s, stock = %s WHERE id = %s"
        rows_affected = execute_update(query, (name, category, float(price), int(stock), pid))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Product updated successfully.'})
        return jsonify({'success': False, 'error': 'Product not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/api/products/<int:pid>', methods=['DELETE'])
@login_required
def delete_product(pid):
    try:
        query = "DELETE FROM products WHERE id = %s"
        rows_affected = execute_update(query, (pid,))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Product deleted successfully.'})
        return jsonify({'success': False, 'error': 'Product not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
