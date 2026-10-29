import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, date

# ==============================================================================
# PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="BizKPI - Business Intelligence & Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished business UI matching the original project aesthetic
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 1.55rem;
        font-weight: 700;
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# DATABASE LAYER (SQLite: Zero-configuration, 100% self-contained for Cloud)
# ==============================================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "bizkpi_local.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes tables and seeds initial data matching the project's schema."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            city TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Products Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Sales Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            sale_date TEXT NOT NULL,
            status TEXT DEFAULT 'Completed',
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)

    # 4. Expenses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Global Sales Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            country TEXT,
            item_type TEXT,
            sales_channel TEXT,
            order_priority TEXT,
            order_date TEXT,
            order_id INTEGER,
            ship_date TEXT,
            units_sold INTEGER,
            unit_price REAL,
            unit_cost REAL,
            total_revenue REAL,
            total_cost REAL,
            total_profit REAL
        )
    """)
    conn.commit()

    # Seed initial Products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ("Baby Food", "Baby Care", 255.28, 120),
            ("Cereal", "Food & Beverage", 205.70, 310),
            ("Office Supplies", "Office", 651.21, 85),
            ("Fruits", "Food & Beverage", 9.33, 500),
            ("Household Cleaners", "Home Care", 668.27, 95),
            ("Vegetables", "Food & Beverage", 154.06, 420),
            ("Personal Care Kit", "Health & Beauty", 81.73, 215),
            ("Cotton Clothes", "Apparel", 109.28, 340),
            ("Luxury Cosmetics", "Beauty", 437.20, 110),
            ("Beverages Pack", "Food & Beverage", 47.45, 450)
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            initial_products
        )
        conn.commit()

    # Seed initial Customers if empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        initial_customers = [
            ("Apex Global Retail", "contact@apexretail.com", "+1-202-555-0143", "New York", "Active"),
            ("Nordic Goods AS", "orders@nordicgoods.no", "+47-22-12-34-56", "Oslo", "Active"),
            ("Pacific Traders Ltd", "pacific@traders.com", "+61-2-9876-5432", "Sydney", "Active"),
            ("Sahara Merchants Inc", "sahara@merchants.com", "+226-25-30-00-00", "Ouagadougou", "Active"),
            ("EuroLogistics GmbH", "info@eurologistics.de", "+49-30-123456", "Berlin", "Active"),
            ("Eastern Gateway Co", "sales@easterngateway.sg", "+65-6789-0123", "Singapore", "Active")
        ]
        cursor.executemany(
            "INSERT INTO customers (name, email, phone, city, status) VALUES (?, ?, ?, ?, ?)",
            initial_customers
        )
        conn.commit()

    # Seed initial Sales if empty
    cursor.execute("SELECT COUNT(*) FROM sales")
    if cursor.fetchone()[0] == 0:
        initial_sales = [
            (1, 1, 10, 255.28, 2552.80, "2026-10-15", "Completed"),
            (2, 2, 25, 205.70, 5142.50, "2026-10-18", "Completed"),
            (3, 3, 5, 651.21, 3256.05, "2026-10-20", "Completed"),
            (4, 7, 30, 81.73, 2451.90, "2026-10-22", "Completed"),
            (5, 8, 40, 109.28, 4371.20, "2026-10-25", "Pending"),
            (6, 9, 8, 437.20, 3497.60, "2026-10-27", "Completed")
        ]
        cursor.executemany(
            "INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount, sale_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            initial_sales
        )
        conn.commit()

    # Seed initial Expenses if empty
    cursor.execute("SELECT COUNT(*) FROM expenses")
    if cursor.fetchone()[0] == 0:
        initial_expenses = [
            ("2026-10-01", "Rent", "Headquarters & Warehouse Lease", 3500.00),
            ("2026-10-05", "Utilities", "Electricity, Water, High-Speed Internet", 620.00),
            ("2026-10-10", "Marketing", "Google Ads & Social Media Campaigns", 1450.00),
            ("2026-10-12", "Logistics", "Freight Shipping & Cargo Transport", 2100.00),
            ("2026-10-15", "Software", "Cloud ERP, CRM & Analytics Subscriptions", 480.00),
            ("2026-10-25", "Payroll", "Sales & Operations Staff Compensation", 5800.00)
        ]
        cursor.executemany(
            "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
            initial_expenses
        )
        conn.commit()

    conn.close()

# Initialize DB on load
init_database()


# ==============================================================================
# DATA LOADING (Global Sales CSV)
# ==============================================================================
@st.cache_data
def load_global_sales():
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "database", "global_sales.csv"),
        os.path.join("database", "global_sales.csv"),
        "global_sales.csv"
    ]
    file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            file_path = p
            break

    if not file_path:
        return pd.DataFrame()

    df = pd.read_csv(file_path)
    df.columns = [c.strip() for c in df.columns]
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')

    numeric_cols = ['Units Sold', 'Unit Price', 'Unit Cost', 'Total Revenue', 'Total Cost', 'Total Profit']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    df['Profit Margin (%)'] = (df['Total Profit'] / df['Total Revenue'].replace(0, 1)) * 100
    return df

global_df = load_global_sales()


# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown("## 📊 BizKPI Portal")
    st.caption("Enterprise KPI & Business Intelligence")
    st.divider()

    selected_nav = st.radio(
        "Navigation Menu",
        [
            "📈 Executive Dashboard",
            "♟ Customers",
            "▣ Products Management",
            "🛒 Sales Transactions",
            "▤ Expenses Tracker",
            "▥ Financial Reports",
            "📋 Global Sales Dataset"
        ],
        index=0
    )

    st.divider()
    st.markdown("### 🏢 System Status")
    st.success("🟢 System Online & Healthy")
    st.caption("Database: SQLite Engine (Self-contained)")
    st.caption(f"Historical Records: **{len(global_df):,}** orders")
    st.markdown("---")
    st.caption("© 2026 BizKPI Analytics Suite")


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if selected_nav == "📈 Executive Dashboard":
    st.markdown("## 📈 Executive Business KPI Dashboard")
    st.caption("Real-time revenue, expense, and order intelligence synthesized across operational data.")

    conn = get_db()
    total_sales_val = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE status = 'Completed'").fetchone()[0]
    total_expenses_val = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]
    total_customers_cnt = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()

    if not global_df.empty:
        hist_revenue = global_df['Total Revenue'].sum()
        hist_cost = global_df['Total Cost'].sum()
        hist_profit = global_df['Total Profit'].sum()
        total_orders = len(global_df)
        avg_margin = (hist_profit / hist_revenue * 100) if hist_revenue > 0 else 0
    else:
        hist_revenue, hist_cost, hist_profit, total_orders, avg_margin = 0, 0, 0, 0, 0

    if avg_margin >= 30:
        st.success(f"💡 **Strong Profitability:** Global profit margin is robust at **{avg_margin:.1f}%** with **${hist_profit:,.2f}** in historical profit and **${total_sales_val:,.2f}** in active completed sales.")
    else:
        st.info(f"💡 **Stable Performance:** Current margin is **{avg_margin:.1f}%**. Review expense trends to optimize net cash flow.")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Historical Revenue", f"${hist_revenue:,.0f}")
    k2.metric("Historical Cost", f"${hist_cost:,.0f}")
    k3.metric("Net Profit", f"${hist_profit:,.0f}")
    k4.metric("Profit Margin", f"{avg_margin:.1f}%")
    k5.metric("Active Customers", f"{total_customers_cnt}")
    k6.metric("Active Expenses", f"${total_expenses_val:,.2f}")

    st.divider()

    with st.expander("🔍 Filter Dashboard Data", expanded=False):
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            all_regions = sorted(global_df['Region'].dropna().unique().tolist()) if not global_df.empty else []
            sel_regions = st.multiselect("Region", options=all_regions, default=all_regions)
        with c_f2:
            all_items = sorted(global_df['Item Type'].dropna().unique().tolist()) if not global_df.empty else []
            sel_items = st.multiselect("Item Type", options=all_items, default=all_items)
        with c_f3:
            all_channels = sorted(global_df['Sales Channel'].dropna().unique().tolist()) if not global_df.empty else []
            sel_channels = st.multiselect("Sales Channel", options=all_channels, default=all_channels)

    f_df = global_df.copy()
    if sel_regions:
        f_df = f_df[f_df['Region'].isin(sel_regions)]
    if sel_items:
        f_df = f_df[f_df['Item Type'].isin(sel_items)]
    if sel_channels:
        f_df = f_df[f_df['Sales Channel'].isin(sel_channels)]

    col_chart_left, col_chart_right = st.columns([1.3, 1])

    with col_chart_left:
        st.markdown("#### 📅 Monthly Revenue & Profit Trends")
        if not f_df.empty:
            monthly = f_df.groupby('YearMonth')[['Total Revenue', 'Total Cost', 'Total Profit']].sum().reset_index()
            fig_trends = go.Figure()
            fig_trends.add_trace(go.Scatter(x=monthly['YearMonth'], y=monthly['Total Revenue'], mode='lines+markers', name='Revenue', line=dict(color='#2563eb', width=3)))
            fig_trends.add_trace(go.Scatter(x=monthly['YearMonth'], y=monthly['Total Cost'], mode='lines+markers', name='Cost', line=dict(color='#ef4444', width=2, dash='dot')))
            fig_trends.add_trace(go.Scatter(x=monthly['YearMonth'], y=monthly['Total Profit'], mode='lines+markers', name='Profit', line=dict(color='#10b981', width=3)))
            fig_trends.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=25, b=10), hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
            st.plotly_chart(fig_trends, use_container_width=True)

    with col_chart_right:
        st.markdown("#### 🛍️ Revenue by Sales Channel")
        if not f_df.empty:
            chan_df = f_df.groupby('Sales Channel')['Total Revenue'].sum().reset_index()
            fig_chan = px.pie(chan_df, values='Total Revenue', names='Sales Channel', hole=0.45, color_discrete_sequence=['#3b82f6', '#10b981'])
            fig_chan.update_layout(margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_chan, use_container_width=True)

    c_sub1, c_sub2 = st.columns(2)
    with c_sub1:
        st.markdown("#### 📦 Revenue by Product Category")
        if not f_df.empty:
            item_rev = f_df.groupby('Item Type')['Total Revenue'].sum().reset_index().sort_values('Total Revenue', ascending=True)
            fig_bar = px.bar(item_rev, y='Item Type', x='Total Revenue', orientation='h', color='Total Revenue', color_continuous_scale='Blues')
            fig_bar.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=20, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    with c_sub2:
        st.markdown("#### 🌍 Geographic Sales Distribution")
        if not f_df.empty:
            reg_df = f_df.groupby('Region')['Total Revenue'].sum().reset_index().sort_values('Total Revenue', ascending=False)
            fig_reg = px.bar(reg_df, x='Region', y='Total Revenue', color='Region')
            fig_reg.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
            st.plotly_chart(fig_reg, use_container_width=True)


# ==============================================================================
# VIEW 2: CUSTOMERS DIRECTORY
# ==============================================================================
elif selected_nav == "♟ Customers":
    st.markdown("## ♟ Customer Directory")
    st.caption("Manage client relationships, contact profiles, and customer statuses.")

    conn = get_db()
    customers_df = pd.read_sql_query("SELECT id, name, email, phone, city, status, created_at FROM customers ORDER BY id DESC", conn)

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Total Customers", len(customers_df))
    active_cnt = len(customers_df[customers_df['status'] == 'Active']) if not customers_df.empty else 0
    c_m2.metric("Active Customers", active_cnt)
    c_m3.metric("Retention / Active Rate", f"{(active_cnt / len(customers_df) * 100):.0f}%" if len(customers_df) > 0 else "0%")

    st.divider()
    tab_cust_list, tab_cust_add = st.tabs(["📋 Customer Records", "➕ Register New Customer"])

    with tab_cust_list:
        search_cust = st.text_input("🔍 Search Customers by Name, City or Email", placeholder="e.g. Apex, Oslo, info@...")
        filtered_cust = customers_df.copy()
        if search_cust:
            mask = (
                filtered_cust['name'].str.contains(search_cust, case=False, na=False) |
                filtered_cust['city'].str.contains(search_cust, case=False, na=False) |
                filtered_cust['email'].str.contains(search_cust, case=False, na=False)
            )
            filtered_cust = filtered_cust[mask]

        st.dataframe(filtered_cust, use_container_width=True, hide_index=True)

    with tab_cust_add:
        st.markdown("#### Register a New Customer Profile")
        with st.form("add_customer_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                new_c_name = st.text_input("Customer / Company Name *")
                new_c_email = st.text_input("Email Address *")
            with f_col2:
                new_c_phone = st.text_input("Phone Number")
                new_c_city = st.text_input("City / Headquarters")
            new_c_status = st.selectbox("Status", ["Active", "Inactive"], index=0)

            submitted = st.form_submit_button("💾 Save Customer Profile", use_container_width=True)
            if submitted:
                if not new_c_name or not new_c_email:
                    st.error("Name and Email are mandatory fields.")
                else:
                    try:
                        c_cursor = conn.cursor()
                        c_cursor.execute(
                            "INSERT INTO customers (name, email, phone, city, status) VALUES (?, ?, ?, ?, ?)",
                            (new_c_name.strip(), new_c_email.strip(), new_c_phone.strip(), new_c_city.strip(), new_c_status)
                        )
                        conn.commit()
                        st.success(f"Customer **{new_c_name}** successfully added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving customer: {e}")
    conn.close()


# ==============================================================================
# VIEW 3: PRODUCTS MANAGEMENT (CRUD)
# ==============================================================================
elif selected_nav == "▣ Products Management":
    st.markdown("## ▣ Product Catalog & Inventory Management")
    st.caption("Add, update stock, modify pricing, and track product catalog inventory.")

    conn = get_db()
    products_df = pd.read_sql_query("SELECT id, name, category, price, stock, created_at FROM products ORDER BY id ASC", conn)

    total_prods = len(products_df)
    total_stock = products_df['stock'].sum() if not products_df.empty else 0
    avg_price = products_df['price'].mean() if not products_df.empty else 0
    inv_value = (products_df['price'] * products_df['stock']).sum() if not products_df.empty else 0

    p_c1, p_c2, p_c3, p_c4 = st.columns(4)
    p_c1.metric("Total Catalog Items", f"{total_prods}")
    p_c2.metric("Total Stock Units", f"{total_stock:,}")
    p_c3.metric("Average Price", f"${avg_price:.2f}")
    p_c4.metric("Inventory Valuation", f"${inv_value:,.2f}")

    st.divider()
    tab_prod_list, tab_prod_add, tab_prod_edit = st.tabs(["📦 Product Inventory", "➕ Add New Product", "⚙️ Update / Delete Product"])

    with tab_prod_list:
        display_prod = products_df.copy()
        if not display_prod.empty:
            display_prod['Code'] = display_prod['id'].apply(lambda x: f"PR-{x:03d}")
            display_prod['Price ($)'] = display_prod['price'].map('${:,.2f}'.format)
            display_prod['Stock Units'] = display_prod['stock'].map('{:,}'.format)
            st.dataframe(
                display_prod[['Code', 'name', 'category', 'Price ($)', 'Stock Units', 'created_at']],
                use_container_width=True,
                hide_index=True
            )

    with tab_prod_add:
        st.markdown("#### Add a New Product to Catalog")
        with st.form("add_product_form", clear_on_submit=True):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                p_name = st.text_input("Product Name *", placeholder="e.g. Ergonomic Office Chair")
                p_category = st.selectbox("Category *", ["Office", "Food & Beverage", "Home Care", "Health & Beauty", "Apparel", "Beauty", "Electronics", "Other"])
            with col_a2:
                p_price = st.number_input("Unit Price ($) *", min_value=0.01, value=49.99, step=1.0)
                p_stock = st.number_input("Initial Stock Units", min_value=0, value=100, step=10)

            p_submit = st.form_submit_button("➕ Add Product to Inventory", use_container_width=True)
            if p_submit:
                if not p_name:
                    st.error("Please enter a valid product name.")
                else:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", (p_name.strip(), p_category, p_price, int(p_stock)))
                    conn.commit()
                    st.success(f"Product **{p_name}** added successfully!")
                    st.rerun()

    with tab_prod_edit:
        st.markdown("#### Update Price / Stock or Delete Product")
        if not products_df.empty:
            prod_options = {f"PR-{r['id']:03d} | {r['name']} (${r['price']:.2f}, Stock: {r['stock']})": r['id'] for _, r in products_df.iterrows()}
            selected_prod_label = st.selectbox("Select Product to Modify", list(prod_options.keys()))
            selected_prod_id = prod_options[selected_prod_label]
            curr_row = products_df[products_df['id'] == selected_prod_id].iloc[0]

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_price = st.number_input("Update Price ($)", min_value=0.01, value=float(curr_row['price']), step=1.0)
            with col_e2:
                new_stock = st.number_input("Update Stock Count", min_value=0, value=int(curr_row['stock']), step=5)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Save Product Updates", use_container_width=True):
                    conn.cursor().execute("UPDATE products SET price = ?, stock = ? WHERE id = ?", (new_price, int(new_stock), selected_prod_id))
                    conn.commit()
                    st.success("Product updated successfully!")
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ Delete Product", type="secondary", use_container_width=True):
                    conn.cursor().execute("DELETE FROM products WHERE id = ?", (selected_prod_id,))
                    conn.commit()
                    st.warning("Product removed from database.")
                    st.rerun()
    conn.close()


# ==============================================================================
# VIEW 4: SALES TRANSACTIONS (CRUD)
# ==============================================================================
elif selected_nav == "🛒 Sales Transactions":
    st.markdown("## 🛒 Sales Order Management")
    st.caption("Record new customer purchases, verify inventory availability, and update fulfillment statuses.")

    conn = get_db()
    sales_query = """
        SELECT s.id, c.name AS customer_name, p.name AS product_name, s.quantity, s.unit_price, s.total_amount, s.sale_date, s.status
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
        ORDER BY s.id DESC
    """
    sales_df = pd.read_sql_query(sales_query, conn)

    completed_sales = sales_df[sales_df['status'] == 'Completed']
    tot_sales_vol = completed_sales['total_amount'].sum() if not completed_sales.empty else 0
    tot_orders_cnt = len(sales_df)
    pending_cnt = len(sales_df[sales_df['status'] == 'Pending'])

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Completed Revenue", f"${tot_sales_vol:,.2f}")
    sc2.metric("Total Orders Logged", f"{tot_orders_cnt}")
    sc3.metric("Pending Fulfillment", f"{pending_cnt}")

    st.divider()
    tab_sales_list, tab_sales_add = st.tabs(["📑 Sales Order Ledger", "➕ Log New Order"])

    with tab_sales_list:
        if not sales_df.empty:
            sales_display = sales_df.copy()
            sales_display['Order No'] = sales_display['id'].apply(lambda x: f"ORD-{x:04d}")
            sales_display['Unit Price'] = sales_display['unit_price'].map('${:,.2f}'.format)
            sales_display['Total Amount'] = sales_display['total_amount'].map('${:,.2f}'.format)
            st.dataframe(
                sales_display[['Order No', 'customer_name', 'product_name', 'quantity', 'Unit Price', 'Total Amount', 'sale_date', 'status']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No sales transactions currently recorded.")

    with tab_sales_add:
        st.markdown("#### Create a New Customer Sale")
        customers_list = conn.execute("SELECT id, name FROM customers WHERE status = 'Active'").fetchall()
        products_list = conn.execute("SELECT id, name, price, stock FROM products WHERE stock > 0").fetchall()

        if not customers_list or not products_list:
            st.warning("You need at least one Active Customer and one Product in stock to record a sale.")
        else:
            cust_dict = {f"{c['name']} (ID: {c['id']})": c['id'] for c in customers_list}
            prod_dict = {f"{p['name']} (Stock: {p['stock']} | ${p['price']:.2f})": (p['id'], p['price'], p['stock']) for p in products_list}

            with st.form("create_sale_form", clear_on_submit=True):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    sel_cust_label = st.selectbox("Select Customer *", list(cust_dict.keys()))
                    sel_prod_label = st.selectbox("Select Product *", list(prod_dict.keys()))
                with col_s2:
                    prod_id, prod_price, max_stock = prod_dict[sel_prod_label]
                    order_qty = st.number_input("Quantity *", min_value=1, max_value=max_stock, value=1, step=1)
                    order_date = st.date_input("Order Date", value=date.today())
                
                order_status = st.selectbox("Fulfillment Status", ["Completed", "Pending"], index=0)
                calc_total = order_qty * prod_price
                st.info(f"💵 **Calculated Order Total:** ${calc_total:,.2f} ({order_qty} units @ ${prod_price:.2f})")

                submit_sale = st.form_submit_button("🛒 Complete Order & Update Stock", use_container_width=True)
                if submit_sale:
                    try:
                        cursor = conn.cursor()
                        cust_id = cust_dict[sel_cust_label]
                        cursor.execute(
                            "INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount, sale_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (cust_id, prod_id, int(order_qty), prod_price, calc_total, str(order_date), order_status)
                        )
                        if order_status == "Completed":
                            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (int(order_qty), prod_id))
                        conn.commit()
                        st.success("Sale order recorded and stock successfully updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to record sale: {e}")
    conn.close()


# ==============================================================================
# VIEW 5: EXPENSES TRACKER (CRUD)
# ==============================================================================
elif selected_nav == "▤ Expenses Tracker":
    st.markdown("## ▤ Operational Expenses Tracker")
    st.caption("Record overhead, logistics, and operational expenditures for net profit calculations.")

    conn = get_db()
    expenses_df = pd.read_sql_query("SELECT id, date, category, description, amount, created_at FROM expenses ORDER BY id DESC", conn)

    total_exp = expenses_df['amount'].sum() if not expenses_df.empty else 0
    top_cat = expenses_df.groupby('category')['amount'].sum().idxmax() if not expenses_df.empty else "N/A"
    avg_entry = expenses_df['amount'].mean() if not expenses_df.empty else 0

    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("Total Operational Expenses", f"${total_exp:,.2f}")
    ec2.metric("Highest Expense Category", top_cat)
    ec3.metric("Average Expense Entry", f"${avg_entry:,.2f}")

    st.divider()
    tab_exp_list, tab_exp_add = st.tabs(["📋 Expense Log", "➕ Log New Expense"])

    with tab_exp_list:
        if not expenses_df.empty:
            c_exp_chart, c_exp_tbl = st.columns([1, 1.2])
            with c_exp_chart:
                cat_chart = expenses_df.groupby('category')['amount'].sum().reset_index()
                fig_exp = px.pie(cat_chart, values='amount', names='category', hole=0.4, title="Expense Allocation by Category")
                fig_exp.update_layout(margin=dict(l=10, r=10, t=35, b=10))
                st.plotly_chart(fig_exp, use_container_width=True)
            with c_exp_tbl:
                disp_exp = expenses_df.copy()
                disp_exp['Expense ID'] = disp_exp['id'].apply(lambda x: f"EXP-{x:03d}")
                disp_exp['Amount ($)'] = disp_exp['amount'].map('${:,.2f}'.format)
                st.dataframe(disp_exp[['Expense ID', 'date', 'category', 'description', 'Amount ($)']], use_container_width=True, hide_index=True)
        else:
            st.info("No expense entries logged yet.")

    with tab_exp_add:
        st.markdown("#### Record a Business Expense")
        with st.form("add_expense_form", clear_on_submit=True):
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                e_date = st.date_input("Expense Date", value=date.today())
                e_category = st.selectbox("Category *", ["Rent", "Utilities", "Marketing", "Logistics", "Software", "Payroll", "Office Supplies", "Insurance", "Other"])
            with col_ex2:
                e_amount = st.number_input("Amount ($) *", min_value=0.01, value=250.00, step=10.0)
                e_desc = st.text_input("Description / Notes", placeholder="e.g. Monthly cloud hosting")

            e_submit = st.form_submit_button("💾 Save Expense Entry", use_container_width=True)
            if e_submit:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)", (str(e_date), e_category, e_desc.strip(), float(e_amount)))
                conn.commit()
                st.success("Expense logged successfully!")
                st.rerun()
    conn.close()


# ==============================================================================
# VIEW 6: FINANCIAL REPORTS & EXPORT
# ==============================================================================
elif selected_nav == "▥ Financial Reports":
    st.markdown("## ▥ Financial Performance Reports")
    st.caption("Generate executive financial summaries, compute net profit margins, and export reports.")

    conn = get_db()
    sales_df = pd.read_sql_query("SELECT total_amount, sale_date FROM sales WHERE status = 'Completed'", conn)
    expenses_df = pd.read_sql_query("SELECT amount, date FROM expenses", conn)
    conn.close()

    total_rev = sales_df['total_amount'].sum() if not sales_df.empty else 0
    total_exp = expenses_df['amount'].sum() if not expenses_df.empty else 0
    net_operating_profit = total_rev - total_exp
    operating_margin = (net_operating_profit / total_rev * 100) if total_rev > 0 else 0

    st.markdown("### Executive Financial Summary")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Gross Sales Revenue", f"${total_rev:,.2f}")
    r2.metric("Total Operating Expenses", f"${total_exp:,.2f}")
    r3.metric("Net Operating Profit", f"${net_operating_profit:,.2f}", delta=f"{operating_margin:.1f}% Margin")
    r4.metric("Operating Health", "Profitable" if net_operating_profit >= 0 else "Operating Deficit")

    st.divider()
    st.markdown("#### 📥 Export Operational Data")
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        if not sales_df.empty:
            csv_sales = sales_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Sales Ledger (CSV)",
                data=csv_sales,
                file_name="bizkpi_sales_report.csv",
                mime="text/csv",
                use_container_width=True
            )
    with c_dl2:
        if not expenses_df.empty:
            csv_exp = expenses_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Expenses Ledger (CSV)",
                data=csv_exp,
                file_name="bizkpi_expenses_report.csv",
                mime="text/csv",
                use_container_width=True
            )


# ==============================================================================
# VIEW 7: GLOBAL SALES DATASET EXPLORER
# ==============================================================================
elif selected_nav == "📋 Global Sales Dataset":
    st.markdown("## 📋 Global Sales Historical Dataset")
    st.caption("Inspect and export the full historical enterprise dataset powering executive analytics.")

    if global_df.empty:
        st.warning("Historical CSV dataset could not be located in database/global_sales.csv.")
    else:
        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            q_search = st.text_input("🔍 Quick Search by Country, Item Type or Region", placeholder="e.g. Tuvalu, Clothes, Europe")
        with col_q2:
            st.write("")
            st.write("")
            csv_raw = global_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Dataset (CSV)",
                data=csv_raw,
                file_name="global_sales_historical.csv",
                mime="text/csv"
            )

        d_df = global_df.copy()
        if q_search:
            mask = (
                d_df['Country'].astype(str).str.contains(q_search, case=False, na=False) |
                d_df['Item Type'].astype(str).str.contains(q_search, case=False, na=False) |
                d_df['Region'].astype(str).str.contains(q_search, case=False, na=False)
            )
            d_df = d_df[mask]

        st.dataframe(
            d_df[['Order ID', 'Order Date', 'Region', 'Country', 'Item Type', 'Sales Channel', 'Units Sold', 'Total Revenue', 'Total Cost', 'Total Profit']],
            use_container_width=True,
            hide_index=True
        )
