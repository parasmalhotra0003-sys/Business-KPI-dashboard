from flask import Blueprint, request, jsonify
from routes.auth import login_required
from database.connection import execute_query, execute_update

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    try:
        search = request.args.get('search', '').strip()

        if search:
            query = """
                SELECT
                    region,
                    COUNT(*) AS record_count
                FROM global_sales
                WHERE region LIKE %s
                GROUP BY region
                ORDER BY record_count DESC
            """
            term = f"%{search}%"
            rows = execute_query(query, (term,))
        else:
            query = """
                SELECT
                    region,
                    COUNT(*) AS record_count
                FROM global_sales
                GROUP BY region
                ORDER BY record_count DESC
            """
            rows = execute_query(query)

        formatted_rows = [
            [r['region'], int(r['record_count'])]
            for r in rows
        ]

        return jsonify({
            'success': True,
            'data': formatted_rows,
            'total': sum(row[1] for row in formatted_rows)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@customers_bp.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    city = data.get('city', '').strip()
    status = data.get('status', 'Active').strip()
    
    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and Email are required.'}), 400
        
    try:
        query = "INSERT INTO customers (name, email, phone, city, status) VALUES (%s, %s, %s, %s, %s)"
        execute_update(query, (name, email, phone, city, status))
        return jsonify({'success': True, 'message': 'Customer added successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/api/customers/<int:cid>', methods=['PUT'])
@login_required
def update_customer(cid):
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    city = data.get('city', '').strip()
    status = data.get('status', 'Active').strip()
    
    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and Email are required.'}), 400
        
    try:
        query = "UPDATE customers SET name = %s, email = %s, phone = %s, city = %s, status = %s WHERE id = %s"
        rows_affected = execute_update(query, (name, email, phone, city, status, cid))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Customer updated successfully.'})
        return jsonify({'success': False, 'error': 'Customer not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@customers_bp.route('/api/customers/<int:cid>', methods=['DELETE'])
@login_required
def delete_customer(cid):
    try:
        query = "DELETE FROM customers WHERE id = %s"
        rows_affected = execute_update(query, (cid,))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Customer deleted successfully.'})
        return jsonify({'success': False, 'error': 'Customer not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@customers_bp.route('/api/sales-customers', methods=['GET'])
@login_required
def get_sales_customers():
    try:
        rows = execute_query(
            "SELECT id, name FROM customers ORDER BY name"
        )
        return jsonify({
            'success': True,
            'data': [[int(r['id']), r['name']] for r in rows]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
