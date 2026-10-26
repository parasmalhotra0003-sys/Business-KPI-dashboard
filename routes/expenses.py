from flask import Blueprint, request, jsonify
from routes.auth import login_required
from database.connection import execute_query, execute_update

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    try:
        search = request.args.get('search', '').strip()
        if search:
            query = """SELECT id, date, category, description, amount 
                       FROM expenses 
                       WHERE category LIKE %s OR description LIKE %s
                       ORDER BY id DESC"""
            term = f"%{search}%"
            rows = execute_query(query, (term, term))
        else:
            rows = execute_query("SELECT id, date, category, description, amount FROM expenses ORDER BY id DESC")
            
        # Format matching the client template: ['18 Jul 2026','Rent','Office Rent','€2,500']
        formatted_rows = []
        for r in rows:
            formatted_rows.append([
                r['date'].strftime('%d %b %Y') if hasattr(r['date'], 'strftime') else str(r['date']),
                r['category'],
                r['description'],
                f"${r['amount']:.2f}",
                str(r['id']) # We add id as a hidden column or trailing value so client JS can map edit/delete actions
            ])
            
        return jsonify({'success': True, 'data': formatted_rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expenses_bp.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    data = request.get_json() or request.form
    date_str = data.get('date') # YYYY-MM-DD
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    amount = data.get('amount')
    
    if not date_str or not category or amount is None:
        return jsonify({'success': False, 'error': 'Date, Category and Amount are required.'}), 400
        
    try:
        query = "INSERT INTO expenses (date, category, description, amount) VALUES (%s, %s, %s, %s)"
        execute_update(query, (date_str, category, description, float(amount)))
        return jsonify({'success': True, 'message': 'Expense recorded successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expenses_bp.route('/api/expenses/<int:eid>', methods=['PUT'])
@login_required
def update_expense(eid):
    data = request.get_json() or request.form
    date_str = data.get('date')
    category = data.get('category', '').strip()
    description = data.get('description', '').strip()
    amount = data.get('amount')
    
    if not date_str or not category or amount is None:
        return jsonify({'success': False, 'error': 'Date, Category and Amount are required.'}), 400
        
    try:
        query = "UPDATE expenses SET date = %s, category = %s, description = %s, amount = %s WHERE id = %s"
        rows_affected = execute_update(query, (date_str, category, description, float(amount), eid))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Expense updated successfully.'})
        return jsonify({'success': False, 'error': 'Expense not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@expenses_bp.route('/api/expenses/<int:eid>', methods=['DELETE'])
@login_required
def delete_expense(eid):
    try:
        query = "DELETE FROM expenses WHERE id = %s"
        rows_affected = execute_update(query, (eid,))
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Expense deleted successfully.'})
        return jsonify({'success': False, 'error': 'Expense not found.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
