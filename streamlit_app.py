import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="BizKPI | Business Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 BizKPI")
st.caption("Business Performance KPI Dashboard")

DATA_PATH = Path("database/global_sales.csv")

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

df = None

if DATA_PATH.exists():
    try:
        df = load_data(str(DATA_PATH))
    except Exception as e:
        st.error(f"Could not read the CSV file: {e}")

if df is None:
    uploaded_file = st.file_uploader(
        "Upload your global_sales.csv dataset",
        type=["csv"],
    )
    if uploaded_file is not None:
        df = load_data(uploaded_file)

if df is None:
    st.info(
        "The dataset was not found at database/global_sales.csv. "
        "Upload your CSV above to display the dashboard."
    )
    st.stop()

df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)
st.sidebar.header("Filters")
filtered = df.copy()

if "region" in filtered.columns:
    regions = sorted(filtered["region"].dropna().astype(str).unique())
    selected_regions = st.sidebar.multiselect(
        "Region",
        regions,
        default=regions,
    )
    filtered = filtered[
        filtered["region"].astype(str).isin(selected_regions)
    ]

if "category" in filtered.columns:
    categories = sorted(filtered["category"].dropna().astype(str).unique())
    selected_categories = st.sidebar.multiselect(
        "Category",
        categories,
        default=categories,
    )
    filtered = filtered[
        filtered["category"].astype(str).isin(selected_categories)
    ]

def total(column):
    if column not in filtered.columns:
        return None
    return pd.to_numeric(filtered[column], errors="coerce").sum()

revenue = total("total_revenue")
profit = total("total_profit")
units = total("units_sold")
orders = len(filtered)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"{revenue:,.2f}" if revenue is not None else "N/A")
c2.metric("Total Profit", f"{profit:,.2f}" if profit is not None else "N/A")
c3.metric("Units Sold", f"{units:,.0f}" if units is not None else "N/A")
c4.metric("Sales Records", f"{orders:,}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Revenue by Region")
    if {"region", "total_revenue"}.issubset(filtered.columns):
        chart_data = filtered.copy()
        chart_data["total_revenue"] = pd.to_numeric(
            chart_data["total_revenue"], errors="coerce"
        )
        chart_data = chart_data.groupby("region")["total_revenue"].sum()
        st.bar_chart(chart_data)
    else:
        st.info("Region and total_revenue columns are required for this chart.")

with right:
    st.subheader("Profit by Category")
    if {"category", "total_profit"}.issubset(filtered.columns):
        chart_data = filtered.copy()
        chart_data["total_profit"] = pd.to_numeric(
            chart_data["total_profit"], errors="coerce"
        )
        chart_data = chart_data.groupby("category")["total_profit"].sum()
        st.bar_chart(chart_data)
    else:
        st.info("Category and total_profit columns are required for this chart.")

st.subheader("Sales Data")
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.caption(f"Showing {len(filtered):,} records after filtering.")
