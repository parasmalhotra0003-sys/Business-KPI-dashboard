from datetime import date
from database.connection import execute_query


def get_latest_period():
    """
    Finds the latest month available in the Global Sales dataset.
    This is used instead of date.today(), because the dataset contains
    historical sales data.
    """
    result = execute_query(
        """
        SELECT
            YEAR(MAX(order_date)) AS year,
            MONTH(MAX(order_date)) AS month
        FROM global_sales
        """
    )

    if not result or result[0]['year'] is None:
        return None, None

    return int(result[0]['year']), int(result[0]['month'])


def get_previous_period(year, month):
    """Return previous month and year."""

    if month == 1:
        return year - 1, 12

    return year, month - 1


def calc_growth(current, previous):
    """Calculate percentage growth."""

    current = float(current or 0)
    previous = float(previous or 0)

    if previous == 0:
        return 100.0 if current > 0 else 0.0

    return round(
        ((current - previous) / previous) * 100,
        1
    )


def get_kpi_summary(selected_date=None):
    """
    Calculates dashboard KPIs from the real Global Sales dataset.

    Data source:
        global_sales

    Metrics:
        Total Revenue
        Total Cost
        Total Profit
        Units Sold
        Total Orders
    """

    latest_year, latest_month = get_latest_period()

    if latest_year is None:
        return {
            'total_revenue': 0,
            'total_cost': 0,
            'total_profit': 0,
            'total_units': 0,
            'total_orders': 0,
            'revenue_growth': 0,
            'cost_growth': 0,
            'profit_growth': 0,
            'units_growth': 0,
            'orders_growth': 0,
            'current_revenue': 0,
            'current_cost': 0,
            'current_profit': 0,
            'current_units': 0,
            'current_orders': 0
        }

    prev_year, prev_month = get_previous_period(
        latest_year,
        latest_month
    )

    # ---------------------------------------------------------
    # OVERALL DATASET TOTALS
    # ---------------------------------------------------------

    overall = execute_query(
        """
        SELECT
            COALESCE(SUM(total_revenue), 0) AS revenue,
            COALESCE(SUM(total_cost), 0) AS cost,
            COALESCE(SUM(total_profit), 0) AS profit,
            COALESCE(SUM(units_sold), 0) AS units,
            COUNT(*) AS orders
        FROM global_sales
        """
    )[0]

    total_revenue = float(overall['revenue'] or 0)
    total_cost = float(overall['cost'] or 0)
    total_profit = float(overall['profit'] or 0)
    total_units = int(overall['units'] or 0)
    total_orders = int(overall['orders'] or 0)

    # Customer and expense KPIs
    customer_result = execute_query(
        "SELECT COUNT(*) AS total FROM customers"
    )
    total_customers = int(customer_result[0]['total'] or 0)

    expense_result = execute_query(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
    )
    total_expenses = float(expense_result[0]['total'] or 0)
    # ---------------------------------------------------------
    # LATEST MONTH
    # ---------------------------------------------------------

    current = execute_query(
        """
        SELECT
            COALESCE(SUM(total_revenue), 0) AS revenue,
            COALESCE(SUM(total_cost), 0) AS cost,
            COALESCE(SUM(total_profit), 0) AS profit,
            COALESCE(SUM(units_sold), 0) AS units,
            COUNT(*) AS orders
        FROM global_sales
        WHERE YEAR(order_date) = %s
          AND MONTH(order_date) = %s
        """,
        (latest_year, latest_month)
    )[0]

    current_revenue = float(current['revenue'] or 0)
    current_cost = float(current['cost'] or 0)
    current_profit = float(current['profit'] or 0)
    current_units = int(current['units'] or 0)
    current_orders = int(current['orders'] or 0)

    # ---------------------------------------------------------
    # PREVIOUS MONTH
    # ---------------------------------------------------------

    previous = execute_query(
        """
        SELECT
            COALESCE(SUM(total_revenue), 0) AS revenue,
            COALESCE(SUM(total_cost), 0) AS cost,
            COALESCE(SUM(total_profit), 0) AS profit,
            COALESCE(SUM(units_sold), 0) AS units,
            COUNT(*) AS orders
        FROM global_sales
        WHERE YEAR(order_date) = %s
          AND MONTH(order_date) = %s
        """,
        (prev_year, prev_month)
    )[0]

    previous_revenue = float(previous['revenue'] or 0)
    previous_cost = float(previous['cost'] or 0)
    previous_profit = float(previous['profit'] or 0)
    previous_units = int(previous['units'] or 0)
    previous_orders = int(previous['orders'] or 0)

    # ---------------------------------------------------------
    # GROWTH
    # ---------------------------------------------------------

    revenue_growth = calc_growth(
        current_revenue,
        previous_revenue
    )

    cost_growth = calc_growth(
        current_cost,
        previous_cost
    )

    profit_growth = calc_growth(
        current_profit,
        previous_profit
    )

    units_growth = calc_growth(
        current_units,
        previous_units
    )

    orders_growth = calc_growth(
        current_orders,
        previous_orders
    )

    return {
        # Overall
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'total_units': total_units,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_expenses': total_expenses,

        # Growth
        'revenue_growth': revenue_growth,
        'cost_growth': cost_growth,
        'profit_growth': profit_growth,
        'units_growth': units_growth,
        'orders_growth': orders_growth,

        # Latest month
        'current_revenue': current_revenue,
        'current_cost': current_cost,
        'current_profit': current_profit,
        'current_units': current_units,
        'current_orders': current_orders,

        # Period information
        'latest_year': latest_year,
        'latest_month': latest_month
    }


def get_charts_data():
    """
    Returns dashboard chart data from global_sales.
    """

    # ---------------------------------------------------------
    # 1. MONTHLY REVENUE / COST / PROFIT
    # ---------------------------------------------------------

    trends = execute_query(
        """
        SELECT
            YEAR(order_date) AS year,
            MONTH(order_date) AS month,
            DATE_FORMAT(order_date, '%b %Y') AS month_label,
            SUM(total_revenue) AS revenue,
            SUM(total_cost) AS cost,
            SUM(total_profit) AS profit
        FROM global_sales
        GROUP BY
            YEAR(order_date),
            MONTH(order_date)
        ORDER BY
            year ASC,
            month ASC
        LIMIT 6
        """
    )

    trend_labels = []
    revenue_data = []
    cost_data = []
    profit_data = []

    for row in trends:
        trend_labels.append(row['month_label'])
        revenue_data.append(float(row['revenue'] or 0))
        cost_data.append(float(row['cost'] or 0))
        profit_data.append(float(row['profit'] or 0))

    # ---------------------------------------------------------
    # 2. SALES BY ITEM TYPE
    # ---------------------------------------------------------

    item_type_data = execute_query(
        """
        SELECT
            item_type,
            SUM(total_revenue) AS revenue
        FROM global_sales
        GROUP BY item_type
        ORDER BY revenue DESC
        """
    )

    item_labels = [
        row['item_type']
        for row in item_type_data
    ]

    item_values = [
        float(row['revenue'] or 0)
        for row in item_type_data
    ]

    # ---------------------------------------------------------
    # 3. SALES BY REGION
    # ---------------------------------------------------------

    region_data = execute_query(
        """
        SELECT
            region,
            SUM(total_revenue) AS revenue
        FROM global_sales
        GROUP BY region
        ORDER BY revenue DESC
        """
    )

    region_labels = [
        row['region']
        for row in region_data
    ]

    region_values = [
        float(row['revenue'] or 0)
        for row in region_data
    ]

    # ---------------------------------------------------------
    # 4. SALES CHANNEL
    # ---------------------------------------------------------

    channel_data = execute_query(
        """
        SELECT
            sales_channel,
            SUM(total_revenue) AS revenue
        FROM global_sales
        GROUP BY sales_channel
        ORDER BY revenue DESC
        """
    )

    channel_labels = [
        row['sales_channel']
        for row in channel_data
    ]

    channel_values = [
        float(row['revenue'] or 0)
        for row in channel_data
    ]

    return {
        'trends': {
            'labels': trend_labels,
            'revenue': revenue_data,
            'cost': cost_data,
            'profit': profit_data
        },

        'categories': {
            'labels': item_labels,
            'values': item_values
        },

        'regions': {
            'labels': region_labels,
            'values': region_values
        },

        'channels': {
            'labels': channel_labels,
            'values': channel_values
        }
    }


def get_dashboard_lists():
    """
    Returns top performing items and recent transactions
    from the Global Sales dataset.
    """

    # ---------------------------------------------------------
    # TOP ITEM TYPES
    # ---------------------------------------------------------

    top_items = execute_query(
        """
        SELECT
            item_type,
            SUM(units_sold) AS units,
            SUM(total_revenue) AS revenue,
            SUM(total_profit) AS profit
        FROM global_sales
        GROUP BY item_type
        ORDER BY revenue DESC
        LIMIT 5
        """
    )

    top_items_list = []

    for row in top_items:
        top_items_list.append([
            row['item_type'],
            str(int(row['units'] or 0)),
            f"${float(row['revenue'] or 0):,.2f}",
            f"${float(row['profit'] or 0):,.2f}"
        ])

    # ---------------------------------------------------------
    # RECENT ORDERS
    # ---------------------------------------------------------

    recent_orders = execute_query(
        """
        SELECT
            order_id,
            country,
            item_type,
            order_date,
            sales_channel,
            total_revenue,
            total_profit
        FROM global_sales
        ORDER BY order_date DESC
        LIMIT 5
        """
    )

    recent_orders_list = []

    for row in recent_orders:

        order_date = row['order_date']

        if hasattr(order_date, 'strftime'):
            formatted_date = order_date.strftime(
                '%d %b %Y'
            )
        else:
            formatted_date = str(order_date)

        recent_orders_list.append([
            str(row['order_id']),
            row['country'],
            row['item_type'],
            formatted_date,
            row['sales_channel'],
            f"${float(row['total_revenue'] or 0):,.2f}",
            f"${float(row['total_profit'] or 0):,.2f}"
        ])

    return {
        'top_items': top_items_list,
        'recent_orders': recent_orders_list
    }