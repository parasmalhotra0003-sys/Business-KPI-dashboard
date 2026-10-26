from flask import Blueprint, request, jsonify
from routes.auth import login_required
from database.connection import execute_query, execute_update

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/api/sales', methods=['GET'])
@login_required
def get_sales():
    try:
        search = request.args.get('search', '').strip()
        if search:
            query = """SELECT s.id, c.name as customer_name, s.sale_date, s.total_amount, s.status 
                       FROM sales s
                       JOIN customers c ON s.customer_id = c.id
                       WHERE c.name LIKE %s OR s.status LIKE %s
                       ORDER BY s.id DESC"""
            term = f"%{search}%"
            rows = execute_query(query, (term, term))
        else:
            query = """SELECT s.id, c.name as customer_name, s.sale_date, s.total_amount, s.status 
                       FROM sales s
                       JOIN customers c ON s.customer_id = c.id
                       ORDER BY s.id DESC"""
            rows = execute_query(query)
            
        # Format matching client: ['ORD-1254','John Smith','18 Jul 2026','€1,250','Completed']
        formatted_rows = []
        for r in rows:
            formatted_rows.append([
                f"ORD-{r['id']:04d}",
                r['customer_name'],
                r['sale_date'].strftime('%d %b %Y') if hasattr(r['sale_date'], 'strftime') else str(r['sale_date']),
                f"${r['total_amount']:.2f}",
                r['status']
            ])
            
        return jsonify({'success': True, 'data': formatted_rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales', methods=['POST'])
@login_required
def record_sale():
    data = request.get_json() or request.form
    customer_id = data.get('customer_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    sale_date = data.get('sale_date') # e.g. YYYY-MM-DD
    status = data.get('status', 'Completed')
    
    if not customer_id or not product_id or not quantity or not sale_date:
        return jsonify({'success': False, 'error': 'Customer, Product, Quantity and Date are required.'}), 400
        
    try:
        # Get product price
        product = execute_query("SELECT price, stock FROM products WHERE id = %s", (product_id,), fetchone=True)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found.'}), 404
            
        unit_price = float(product['price'])
        total_amount = unit_price * int(quantity)
        
        # Check stock if completing order
        if status == 'Completed' and product['stock'] < int(quantity):
            return jsonify({'success': False, 'error': f"Insufficient stock. Available: {product['stock']}"}), 400
            
        # Record sale
        query = """INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount, sale_date, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        execute_update(query, (customer_id, product_id, int(quantity), unit_price, total_amount, sale_date, status))
        
        # Deduct stock if Completed
        if status == 'Completed':
            execute_update("UPDATE products SET stock = stock - %s WHERE id = %s", (int(quantity), product_id))
            
        return jsonify({'success': True, 'message': 'Sale recorded successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/<int:sid>', methods=['PUT'])
@login_required
def update_sale(sid):
    data = request.get_json() or request.form
    customer_id = data.get('customer_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    sale_date = data.get('sale_date')
    status = data.get('status')
    
    if not customer_id or not product_id or not quantity or not sale_date or not status:
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400
        
    try:
        # Get old sale details to handle stock reversal
        old_sale = execute_query("SELECT * FROM sales WHERE id = %s", (sid,), fetchone=True)
        if not old_sale:
            return jsonify({'success': False, 'error': 'Sale not found.'}), 404
            
        product = execute_query("SELECT price, stock FROM products WHERE id = %s", (product_id,), fetchone=True)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found.'}), 404
            
        # Revert old stock if old sale was completed
        if old_sale['status'] == 'Completed':
            execute_update("UPDATE products SET stock = stock + %s WHERE id = %s", (old_sale['quantity'], old_sale['product_id']))
            
        # Recalculate price and amount
        unit_price = float(product['price'])
        total_amount = unit_price * int(quantity)
        
        # Fetch updated stock level
        updated_stock = execute_query("SELECT stock FROM products WHERE id = %s", (product_id,), fetchone=True)['stock']
        
        # Check stock for new quantity
        if status == 'Completed' and updated_stock < int(quantity):
            # Rollback: restore old completed stock since update failed
            if old_sale['status'] == 'Completed':
                execute_update("UPDATE products SET stock = stock - %s WHERE id = %s", (old_sale['quantity'], old_sale['product_id']))
            return jsonify({'success': False, 'error': f"Insufficient stock. Available: {updated_stock}"}), 400
            
        # Update sale
        query = """UPDATE sales 
                   SET customer_id = %s, product_id = %s, quantity = %s, unit_price = %s, 
                       total_amount = %s, sale_date = %s, status = %s 
                   WHERE id = %s"""
        execute_update(query, (customer_id, product_id, int(quantity), unit_price, total_amount, sale_date, status, sid))
        
        # Deduct new stock if Completed
        if status == 'Completed':
            execute_update("UPDATE products SET stock = stock - %s WHERE id = %s", (int(quantity), product_id))
            
        return jsonify({'success': True, 'message': 'Sale updated successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/<int:sid>', methods=['DELETE'])
@login_required
def delete_sale(sid):
    try:
        # Revert stock if Completed before deleting
        old_sale = execute_query("SELECT * FROM sales WHERE id = %s", (sid,), fetchone=True)
        if not old_sale:
            return jsonify({'success': False, 'error': 'Sale not found.'}), 404
            
        if old_sale['status'] == 'Completed':
            execute_update("UPDATE products SET stock = stock + %s WHERE id = %s", (old_sale['quantity'], old_sale['product_id']))
            
        execute_update("DELETE FROM sales WHERE id = %s", (sid,))
        return jsonify({'success': True, 'message': 'Sale deleted successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
