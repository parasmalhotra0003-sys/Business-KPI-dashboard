
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="BizKPI - Business Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

.stApp {
    background: #f5f7fb;
    font-family: Inter, Arial, sans-serif;
    color: #172033;
}
[data-testid="stSidebar"] {
    background: linear-gradient(#0b1f36, #0d2945);
}
[data-testid="stSidebar"] * {
    color: #dbe7f5;
}
[data-testid="stSidebar"] h1 {
    color: white;
    font-size: 25px;
    font-weight: 800;
}
[data-testid="stHeader"] {
    background: white;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}
.kpi-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px #1720330a;
    min-height: 125px;
}
.kpi-label {
    color: #7b8798;
    font-size: 12px;
    font-weight: 600;
}
.kpi-value {
    color: #0b1f36;
    font-size: 27px;
    font-weight: 800;
    margin-top: 8px;
}
.section-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 12px;
    padding: 18px;
}
h1, h2, h3 {
    color: #0b1f36;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 2px 8px #1720330a;
}
div[data-testid="stMetricLabel"] {
    color: #7b8798;
}
div[data-testid="stMetricValue"] {
    color: #0b1f36;
    font-weight: 800;
}
.stButton button {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 7px;
}
.stButton button:hover {
    background: #1d4ed8;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("# 📊 BizKPI")
st.sidebar.caption("BUSINESS INTELLIGENCE")
page = st.sidebar.radio(
    "NAVIGATION",
    ["Dashboard", "Customers", "Products", "Sales",
     "Expenses", "Reports", "Profile", "Settings"],
)
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 BizKPI Dashboard")

st.title(page)
st.caption(f"Business Performance / {page}")

data_path = Path("database/global_sales.csv")
df = None

if data_path.exists():
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        st.error(f"Could not load dataset: {e}")

if df is None:
    uploaded = st.file_uploader("Upload global_sales.csv", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)

if df is None:
    st.info("Upload the global_sales.csv dataset to display your dashboard.")
    st.stop()

df.columns = (
    df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
)

if page != "Dashboard":
    st.info(
        f"{page} page selected. The original HTML pages and Flask APIs "
        "have not yet been connected to this Streamlit interface."
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.stop()

filtered = df.copy()
with st.sidebar:
    st.markdown("### FILTERS")
    if "region" in filtered.columns:
        regions = sorted(filtered["region"].dropna().astype(str).unique())
        chosen = st.multiselect("Region", regions, default=regions)
        filtered = filtered[filtered["region"].astype(str).isin(chosen)]
    if "item_type" in filtered.columns:
        categories = sorted(filtered["item_type"].dropna().astype(str).unique())
        chosen_categories = st.multiselect(
            "Item Type", categories, default=categories
        )
        filtered = filtered[
            filtered["item_type"].astype(str).isin(chosen_categories)
        ]

def number_sum(column):
    if column not in filtered.columns:
        return None
    return pd.to_numeric(filtered[column], errors="coerce").sum()

revenue = number_sum("total_revenue")
profit = number_sum("total_profit")
units = number_sum("units_sold")
cost = number_sum("total_cost")

def fmt(value):
    return "N/A" if value is None else f"{value:,.2f}"

a, b, c, d = st.columns(4)
with a:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">TOTAL REVENUE</div>'
        f'<div class="kpi-value">{fmt(revenue)}</div></div>',
        unsafe_allow_html=True,
    )
with b:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">TOTAL PROFIT</div>'
        f'<div class="kpi-value">{fmt(profit)}</div></div>',
        unsafe_allow_html=True,
    )
with c:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">TOTAL COST</div>'
        f'<div class="kpi-value">{fmt(cost)}</div></div>',
        unsafe_allow_html=True,
    )
with d:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">UNITS SOLD</div>'
        f'<div class="kpi-value">{fmt(units)}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
left, right = st.columns([1.5, 1])

with left:
    st.markdown("### Revenue by Region")
    if {"region", "total_revenue"}.issubset(filtered.columns):
        chart = filtered.copy()
        chart["total_revenue"] = pd.to_numeric(
            chart["total_revenue"], errors="coerce"
        )
        chart = chart.groupby("region")["total_revenue"].sum()
        st.bar_chart(chart, color="#2563eb")
    else:
        st.warning("The region or total revenue column is missing.")

with right:
    st.markdown("### Profit by Item Type")
    if {"item_type", "total_profit"}.issubset(filtered.columns):
        chart = filtered.copy()
        chart["total_profit"] = pd.to_numeric(
            chart["total_profit"], errors="coerce"
        )
        chart = chart.groupby("item_type")["total_profit"].sum()
        st.bar_chart(chart, color="#16a34a")
    else:
        st.warning("The item type or total profit column is missing.")

st.write("")
st.markdown("### Sales Data")
st.dataframe(filtered, use_container_width=True, hide_index=True)
st.caption(f"Showing {len(filtered):,} records")
