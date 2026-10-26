from flask import Blueprint, jsonify
from routes.auth import login_required
from services.kpi_service import get_kpi_summary, get_charts_data, get_dashboard_lists

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard', methods=['GET'])
@login_required
def api_dashboard_data():
    """
    Combines KPI summary, chart trends, recent sales, and top products
    into a single JSON payload for the dynamic dashboard rendering.
    """
    try:
        kpis = get_kpi_summary()
        charts = get_charts_data()
        lists = get_dashboard_lists()
        
        # Determine business performance summary text based on profit/revenue growth
        perf_summary = "Business is stable. Review expense trends to optimize profit."
        if kpis['profit_growth'] > 5.0:
            perf_summary = f"Strong performance! Profit has grown by {kpis['profit_growth']}% compared to last month."
        elif kpis['profit_growth'] < -5.0:
            perf_summary = f"Caution: Profit is down by {abs(kpis['profit_growth'])}% this month. Investigate expenses or declining sales."
            
        return jsonify({
            'success': True,
            'kpis': kpis,
            'charts': charts,
            'lists': lists,
            'performance_summary': perf_summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Failed to retrieve dashboard data: {str(e)}"
        }), 500
