import os
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="BizKPI - Business Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit default chrome so your original HTML/CSS project takes 100% of the screen
st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    div[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    iframe {
        border: none !important;
        width: 100% !important;
        height: 100vh !important;
        min-height: 100vh !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# LOAD ORIGINAL PROJECT ASSETS (HTML, CSS, JS)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_asset(subpath):
    full_path = os.path.join(BASE_DIR, subpath)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

css_content = read_asset(os.path.join("static", "css", "styles.css"))
js_content = read_asset(os.path.join("static", "js", "app.js"))
html_template = read_asset(os.path.join("templates", "dashboard.html"))

# ==============================================================================
# CLIENT-SIDE DATA ENGINE (Powers all original tabs, modals & CRUD operations)
# ==============================================================================
api_interceptor = """
<script>
window.APP_STORE = {
    products: [
        ["PR-001", "Wireless Headphones", "Electronics", "$125.00", "320", "$40,000.00"],
        ["PR-002", "Ergonomic Office Chair", "Office", "$249.00", "85", "$21,165.00"],
        ["PR-003", "Cotton Casual Shirt", "Clothing", "$45.00", "410", "$18,450.00"],
        ["PR-004", "Stainless Steel Kettle", "Home Appliances", "$38.00", "150", "$5,700.00"],
        ["PR-005", "Leather Laptop Bag", "Accessories", "$89.00", "195", "$17,355.00"],
        ["PR-006", "Smart Fitness Tracker", "Electronics", "$79.00", "220", "$17,380.00"]
    ],
    customers: [
        ["Europe", 38],
        ["Sub-Saharan Africa", 36],
        ["Asia", 29],
        ["Australia and Oceania", 24],
        ["Central America and the Caribbean", 20],
        ["Middle East and North Africa", 18],
        ["North America", 15]
    ],
    salesCustomers: [
        [1, "Apex Global Retail"],
        [2, "Nordic Goods AS"],
        [3, "Pacific Traders Ltd"],
        [4, "Sahara Merchants Inc"],
        [5, "EuroLogistics GmbH"],
        [6, "Eastern Gateway Co"]
    ],
    sales: [
        ["ORD-1006", "Apex Global Retail", "28 Oct 2026", "$1,250.00", "Completed"],
        ["ORD-1005", "Nordic Goods AS", "27 Oct 2026", "$3,450.00", "Completed"],
        ["ORD-1004", "Pacific Traders Ltd", "25 Oct 2026", "$890.00", "Pending"],
        ["ORD-1003", "Sahara Merchants Inc", "24 Oct 2026", "$4,120.00", "Completed"],
        ["ORD-1002", "EuroLogistics GmbH", "22 Oct 2026", "$2,100.00", "Completed"],
        ["ORD-1001", "Eastern Gateway Co", "20 Oct 2026", "$950.00", "Completed"]
    ],
    expenses: [
        ["28 Oct 2026", "Rent", "Headquarters & Warehouse Lease", "$3,500.00", "1"],
        ["25 Oct 2026", "Salaries", "Sales & Operations Staff Compensation", "$5,800.00", "2"],
        ["20 Oct 2026", "Logistics", "Freight Shipping & Cargo Transport", "$2,100.00", "3"],
        ["15 Oct 2026", "Marketing", "Google Ads & Social Media Campaigns", "$1,450.00", "4"],
        ["10 Oct 2026", "Utilities", "Electricity, Water, High-Speed Internet", "$620.00", "5"],
        ["05 Oct 2026", "Software", "Cloud ERP & Analytics Subscriptions", "$480.00", "6"]
    ]
};

window.fetch = async function(url, options = {}) {
    const urlStr = typeof url === 'string' ? url : (url.url || '');
    const method = (options.method || 'GET').toUpperCase();
    
    // 1. Dashboard API
    if (urlStr.includes('/api/dashboard') || urlStr === window.API_URLS?.dashboard) {
        return new Response(JSON.stringify({
            success: true,
            kpis: {
                total_revenue: 13734841.53,
                total_profit: 44168198.40,
                total_expenses: 13950.00,
                total_customers: 185,
                revenue_growth: 14.8,
                profit_growth: 18.2,
                expense_growth: 2.4,
                customer_growth: 5.0
            },
            charts: {
                trends: {
                    labels: ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026"],
                    revenue: [2100000, 2450000, 2300000, 2800000, 2600000, 3100000],
                    cost: [1450000, 1670000, 1590000, 1910000, 1760000, 2110000],
                    profit: [650000, 780000, 710000, 890000, 840000, 990000]
                },
                categories: {
                    labels: ["Cosmetics", "Clothes", "Baby Food", "Office Supplies", "Household"],
                    values: [3450000, 2900000, 2550000, 2100000, 1850000]
                }
            },
            lists: {
                top_items: [
                    ["Cosmetics", "12,450", "$3,450,000.00", "$1,200,000.00"],
                    ["Clothes", "10,200", "$2,900,000.00", "$950,000.00"],
                    ["Baby Food", "9,800", "$2,550,000.00", "$850,000.00"],
                    ["Office Supplies", "5,400", "$2,100,000.00", "$720,000.00"],
                    ["Household", "4,200", "$1,850,000.00", "$640,000.00"]
                ],
                recent_orders: [
                    ["ORD-1082", "Tuvalu", "Baby Food", "28 Oct 2026", "Offline", "$253,365.40", "$95,141.05"],
                    ["ORD-1081", "Grenada", "Cereal", "27 Oct 2026", "Online", "$57,678.28", "$24,840.63"],
                    ["ORD-1080", "Russia", "Office Supplies", "26 Oct 2026", "Offline", "$115,850.25", "$22,459.87"],
                    ["ORD-1079", "Rwanda", "Office Supplies", "25 Oct 2026", "Offline", "$329,642.50", "$63,907.75"],
                    ["ORD-1078", "Angola", "Household", "24 Oct 2026", "Offline", "$279,804.64", "$69,391.15"]
                ]
            },
            performance_summary: "Strong performance! Profit has grown by 18.2% compared to last month."
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    // 2. Customers API
    if (urlStr.includes('/api/customers')) {
        const urlParams = new URL(urlStr, window.location.origin).searchParams;
        const q = (urlParams.get('search') || '').toLowerCase();
        let rows = window.APP_STORE.customers;
        if (q) rows = rows.filter(r => r[0].toLowerCase().includes(q));
        return new Response(JSON.stringify({ success: true, data: rows }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    // 3. Sales Customer List (dropdowns in modals)
    if (urlStr.includes('/api/sales-customers')) {
        return new Response(JSON.stringify({ success: true, data: window.APP_STORE.salesCustomers }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    // 4. Products API
    if (urlStr.includes('/api/products')) {
        if (method === 'GET') {
            const urlParams = new URL(urlStr, window.location.origin).searchParams;
            const q = (urlParams.get('search') || '').toLowerCase();
            let rows = window.APP_STORE.products;
            if (q) rows = rows.filter(r => r[1].toLowerCase().includes(q) || r[2].toLowerCase().includes(q));
            return new Response(JSON.stringify({ success: true, data: rows }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'POST') {
            const body = JSON.parse(options.body || '{}');
            const newId = `PR-00${window.APP_STORE.products.length + 1}`;
            window.APP_STORE.products.unshift([
                newId,
                body.name || "New Product",
                body.category || "General",
                `$${parseFloat(body.price || 0).toFixed(2)}`,
                String(body.stock || 0),
                `$0.00`
            ]);
            return new Response(JSON.stringify({ success: true, message: "Product added successfully" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'DELETE') {
            const id = urlStr.split('/').pop();
            window.APP_STORE.products = window.APP_STORE.products.filter(p => !p[0].includes(id));
            return new Response(JSON.stringify({ success: true, message: "Product deleted" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
    }

    // 5. Sales API
    if (urlStr.includes('/api/sales')) {
        if (method === 'GET') {
            const urlParams = new URL(urlStr, window.location.origin).searchParams;
            const q = (urlParams.get('search') || '').toLowerCase();
            let rows = window.APP_STORE.sales;
            if (q) rows = rows.filter(r => r[1].toLowerCase().includes(q) || r[4].toLowerCase().includes(q));
            return new Response(JSON.stringify({ success: true, data: rows }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'POST') {
            const body = JSON.parse(options.body || '{}');
            const newOrd = `ORD-${1000 + window.APP_STORE.sales.length + 1}`;
            const custMatch = window.APP_STORE.salesCustomers.find(c => c[0] == body.customer_id);
            const custName = custMatch ? custMatch[1] : "Direct Client";
            window.APP_STORE.sales.unshift([
                newOrd,
                custName,
                body.sale_date || "Today",
                `$${(body.quantity * 50).toFixed(2)}`,
                body.status || "Completed"
            ]);
            return new Response(JSON.stringify({ success: true, message: "Sale recorded successfully" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'DELETE') {
            const id = urlStr.split('/').pop();
            window.APP_STORE.sales = window.APP_STORE.sales.filter(s => !s[0].includes(id));
            return new Response(JSON.stringify({ success: true, message: "Sale deleted" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
    }

    // 6. Expenses API
    if (urlStr.includes('/api/expenses')) {
        if (method === 'GET') {
            const urlParams = new URL(urlStr, window.location.origin).searchParams;
            const q = (urlParams.get('search') || '').toLowerCase();
            let rows = window.APP_STORE.expenses;
            if (q) rows = rows.filter(r => r[1].toLowerCase().includes(q) || r[2].toLowerCase().includes(q));
            return new Response(JSON.stringify({ success: true, data: rows }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'POST') {
            const body = JSON.parse(options.body || '{}');
            window.APP_STORE.expenses.unshift([
                body.date || "Today",
                body.category || "General",
                body.description || "Operational Expense",
                `$${parseFloat(body.amount || 0).toFixed(2)}`,
                String(window.APP_STORE.expenses.length + 1)
            ]);
            return new Response(JSON.stringify({ success: true, message: "Expense recorded successfully" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        } else if (method === 'DELETE') {
            const id = urlStr.split('/').pop();
            window.APP_STORE.expenses = window.APP_STORE.expenses.filter(e => e[4] != id);
            return new Response(JSON.stringify({ success: true, message: "Expense deleted" }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
    }

    // 7. Reports API
    if (urlStr.includes('/api/reports')) {
        return new Response(JSON.stringify({
            success: true,
            kpis: {
                total_revenue: 14760.00,
                total_profit: 8410.00,
                total_expenses: 6350.00,
                total_customers: 6
            },
            chart: {
                labels: ["20 Oct", "22 Oct", "24 Oct", "25 Oct", "27 Oct", "28 Oct"],
                values: [950, 2100, 4120, 890, 3450, 1250]
            }
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    // 8. Profile API
    if (urlStr.includes('/api/auth/profile')) {
        return new Response(JSON.stringify({
            user: { id: 1, username: "Admin User", email: "admin@bizkpi.org", role: "admin" }
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    return new Response(JSON.stringify({ success: true }), { status: 200, headers: { 'Content-Type': 'application/json' } });
};
</script>
"""

# ==============================================================================
# COMPOSE FULL ORIGINAL WEB PAGE (CSS INLINED, JS INLINED, EXACT ORIGINAL DESIGN)
# ==============================================================================
final_html = html_template.replace(
    '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/styles.css\') }}">',
    f"<style>\n{css_content}\n</style>"
)

final_html = final_html.replace("{{ username }}", "Admin User")
final_html = final_html.replace("{{ url_for('dashboard.api_dashboard_data') }}", "/api/dashboard")

api_setup = """
<script>
    window.API_URLS = {
        dashboard: "/api/dashboard",
        customers: "/api/customers",
        products: "/api/products",
        sales: "/api/sales",
        expenses: "/api/expenses",
        reports: "/api/reports",
        profile: "/api/auth/profile",
        logout: "/logout"
    };
</script>
""" + api_interceptor

final_html = final_html.replace(
    'window.API_URLS = {',
    '// window.API_URLS handled\nwindow.ORIGINAL_URLS = {'
)

final_html = final_html.replace(
    '<script src="{{ url_for(\'static\', filename=\'js/app.js\') }}"></script>',
    f"{api_setup}\n<script>\n{js_content}\n</script>"
)

# Render the complete original web application inside Streamlit
components.html(final_html, height=1050, scrolling=True)
