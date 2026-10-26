from flask import Blueprint, request, jsonify, Response
from routes.auth import login_required
from database.connection import execute_query
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports', methods=['GET'])
@login_required
def get_report_data():
    """
    Retrieves dynamic performance analytics based on custom date filters.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base WHERE clauses
    sales_where = "WHERE s.status = 'Completed'"
    expenses_where = "WHERE 1=1"
    params = []
    
    if start_date and end_date:
        sales_where += " AND s.sale_date BETWEEN %s AND %s"
        expenses_where += " AND date BETWEEN %s AND %s"
        params = [start_date, end_date]
        
    try:
        # 1. Totals in range
        rev_query = f"SELECT SUM(total_amount) as total FROM sales s {sales_where}"
        exp_query = f"SELECT SUM(amount) as total FROM expenses {expenses_where}"
        
        # Double the params for two separate queries
        revenue = execute_query(rev_query, params)[0]['total'] or 0.0
        expenses = execute_query(exp_query, params)[0]['total'] or 0.0
        profit = float(revenue) - float(expenses)
        
        # Customer count in range
        cust_query = f"SELECT COUNT(DISTINCT customer_id) as count FROM sales s {sales_where}"
        customers = execute_query(cust_query, params)[0]['count'] or 0
        
        # 2. Daily breakdown for the chart
        # Determine format based on range size
        breakdown_query = f"""
            SELECT DATE_FORMAT(sale_date, '%d %b') as label, SUM(total_amount) as value, MIN(sale_date) as sort_date
            FROM sales s
            {sales_where}
            GROUP BY label
            ORDER BY sort_date ASC
            LIMIT 15
        """
        breakdown_data = execute_query(breakdown_query, params)
        
        chart_labels = [row['label'] for row in breakdown_data]
        chart_values = [float(row['value']) for row in breakdown_data]
        
        # If empty breakdown, seed some labels
        if not chart_labels:
            chart_labels = ["No Data"]
            chart_values = [0.0]
            
        return jsonify({
            'success': True,
            'kpis': {
                'total_revenue': float(revenue),
                'total_expenses': float(expenses),
                'total_profit': float(profit),
                'total_customers': customers
            },
            'chart': {
                'labels': chart_labels,
                'values': chart_values
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/export', methods=['GET'])
@login_required
def export_csv_report():
    """
    Generates a downloadable CSV summary of sales activity.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = """
        SELECT s.id, c.name as customer_name, p.name as product_name, 
               s.quantity, s.unit_price, s.total_amount, s.sale_date, s.status
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
    """
    params = []
    
    if start_date and end_date:
        query += " WHERE s.sale_date BETWEEN %s AND %s"
        params = [start_date, end_date]
        
    query += " ORDER BY s.sale_date DESC"
    
    try:
        rows = execute_query(query, params)
        
        # Generate CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Order ID', 'Customer Name', 'Product Name', 'Quantity', 'Unit Price', 'Total Amount', 'Sale Date', 'Status'])
        
        # Rows
        for r in rows:
            writer.writerow([
                f"ORD-{r['id']:04d}",
                r['customer_name'],
                r['product_name'],
                r['quantity'],
                float(r['unit_price']),
                float(r['total_amount']),
                str(r['sale_date']),
                r['status']
            ])
            
        csv_data = output.getvalue()
        output.close()
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=bizkpi_sales_report.csv"}
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
