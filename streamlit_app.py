import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="BizKPI - Business Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA LOADING & CACHING
# ==========================================
@st.cache_data
def load_data():
    # Potential paths for the CSV
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
        st.error("Error: Could not locate 'global_sales.csv' in database/ or current directory.")
        return pd.DataFrame()

    df = pd.read_csv(file_path)

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Convert date columns
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')

    # Ensure numeric columns
    numeric_cols = ['Units Sold', 'Unit Price', 'Unit Cost', 'Total Revenue', 'Total Cost', 'Total Profit']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Derived fields
    df['Year'] = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.month
    df['YearMonth'] = df['Order Date'].dt.to_period('M').astype(str)
    df['Profit Margin (%)'] = (df['Total Profit'] / df['Total Revenue'].replace(0, 1)) * 100

    return df

raw_df = load_data()

if raw_df.empty:
    st.stop()

# ==========================================
# SIDEBAR FILTERS
# ==========================================
with st.sidebar:
    st.title("📊 BizKPI Dashboard")
    st.markdown("Business Performance & Sales Intelligence")
    st.divider()

    st.subheader("Filter Data")

    # Date Range Filter
    min_date = raw_df['Order Date'].min().date()
    max_date = raw_df['Order Date'].max().date()
    
    date_range = st.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Region Filter
    all_regions = sorted(raw_df['Region'].dropna().unique().tolist())
    selected_regions = st.multiselect(
        "Region",
        options=all_regions,
        default=all_regions
    )

    # Item Type Filter
    all_items = sorted(raw_df['Item Type'].dropna().unique().tolist())
    selected_items = st.multiselect(
        "Item Type",
        options=all_items,
        default=all_items
    )

    # Channel Filter
    all_channels = sorted(raw_df['Sales Channel'].dropna().unique().tolist())
    selected_channels = st.multiselect(
        "Sales Channel",
        options=all_channels,
        default=all_channels
    )

    # Priority Filter
    all_priorities = sorted(raw_df['Order Priority'].dropna().unique().tolist())
    selected_priorities = st.multiselect(
        "Order Priority",
        options=all_priorities,
        default=all_priorities
    )

    st.divider()
    st.info(f"Showing **{len(raw_df)}** historical records.")
    st.markdown("© 2026 BizKPI Analytics")

# ==========================================
# APPLY FILTERS
# ==========================================
df = raw_df.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['Order Date'].dt.date >= start_date) & (df['Order Date'].dt.date <= end_date)]

if selected_regions:
    df = df[df['Region'].isin(selected_regions)]

if selected_items:
    df = df[df['Item Type'].isin(selected_items)]

if selected_channels:
    df = df[df['Sales Channel'].isin(selected_channels)]

if selected_priorities:
    df = df[df['Order Priority'].isin(selected_priorities)]

if df.empty:
    st.warning("No records match the selected filter criteria. Please adjust your filters.")
    st.stop()

# ==========================================
# OVERALL METRICS CALCULATION
# ==========================================
total_revenue = df['Total Revenue'].sum()
total_cost = df['Total Cost'].sum()
total_profit = df['Total Profit'].sum()
total_units = df['Units Sold'].sum()
total_orders = len(df)
avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

# Automated Business Performance Insight
if avg_margin >= 30:
    summary_type = "success"
    perf_message = f"**Strong Profitability:** The business is generating a healthy **{avg_margin:.1f}% profit margin** with **${total_profit:,.2f}** in net profit."
elif avg_margin >= 15:
    summary_type = "info"
    perf_message = f"**Stable Performance:** Profit margin is at **{avg_margin:.1f}%**. Review item costs and shipping channels to optimize net profit."
else:
    summary_type = "warning"
    perf_message = f"**Margin Alert:** Current profit margin is compressed at **{avg_margin:.1f}%**. Investigate high unit costs and lower-margin items."

# ==========================================
# HEADER & INSIGHT BANNER
# ==========================================
st.markdown("## 📈 Business Executive KPI Dashboard")
st.caption("Real-time revenue, expense, and order analytics across global markets.")

if summary_type == "success":
    st.success(perf_message)
elif summary_type == "info":
    st.info(perf_message)
else:
    st.warning(perf_message)

# KPI Metrics Row
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Revenue", f"${total_revenue:,.0f}")
c2.metric("Total Cost", f"${total_cost:,.0f}")
c3.metric("Total Profit", f"${total_profit:,.0f}")
c4.metric("Profit Margin", f"{avg_margin:.1f}%")
c5.metric("Units Sold", f"{total_units:,.0f}")
c6.metric("Total Orders", f"{total_orders:,}")

st.divider()

# ==========================================
# DASHBOARD TABS
# ==========================================
tab_overview, tab_products, tab_geography, tab_data = st.tabs([
    "📊 Financial Overview",
    "📦 Products & Categories",
    "🌍 Geographic Intelligence",
    "📋 Data Explorer & Export"
])

# ------------------------------------------
# TAB 1: FINANCIAL OVERVIEW
# ------------------------------------------
with tab_overview:
    # Monthly Trends
    st.subheader("Monthly Financial Trends")
    monthly_df = df.groupby('YearMonth')[['Total Revenue', 'Total Cost', 'Total Profit']].sum().reset_index()
    monthly_df = monthly_df.sort_values('YearMonth')

    fig_trends = go.Figure()
    fig_trends.add_trace(go.Scatter(
        x=monthly_df['YearMonth'], y=monthly_df['Total Revenue'],
        mode='lines+markers', name='Revenue',
        line=dict(color='#2563eb', width=3),
        marker=dict(size=7)
    ))
    fig_trends.add_trace(go.Scatter(
        x=monthly_df['YearMonth'], y=monthly_df['Total Cost'],
        mode='lines+markers', name='Cost',
        line=dict(color='#ef4444', width=2, dash='dot'),
        marker=dict(size=6)
    ))
    fig_trends.add_trace(go.Scatter(
        x=monthly_df['YearMonth'], y=monthly_df['Total Profit'],
        mode='lines+markers', name='Profit',
        line=dict(color='#10b981', width=3),
        marker=dict(size=7)
    ))
    fig_trends.update_layout(
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trends, use_container_width=True)

    col_ch1, col_ch2 = st.columns(2)

    with col_ch1:
        st.subheader("Sales by Channel")
        channel_df = df.groupby('Sales Channel')['Total Revenue'].sum().reset_index()
        fig_channel = px.pie(
            channel_df, values='Total Revenue', names='Sales Channel',
            hole=0.45,
            color_discrete_sequence=['#3b82f6', '#10b981']
        )
        fig_channel.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_channel, use_container_width=True)

    with col_ch2:
        st.subheader("Orders by Priority")
        priority_df = df.groupby('Order Priority')['Units Sold'].sum().reset_index()
        fig_priority = px.bar(
            priority_df, x='Order Priority', y='Units Sold',
            color='Order Priority',
            color_discrete_sequence=px.colors.qualitative.Safe,
            text_auto=True
        )
        fig_priority.update_layout(
            template="plotly_white",
            showlegend=False,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_priority, use_container_width=True)

# ------------------------------------------
# TAB 2: PRODUCTS & CATEGORIES
# ------------------------------------------
with tab_products:
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.subheader("Revenue by Item Type")
        item_rev = df.groupby('Item Type')[['Total Revenue', 'Total Profit']].sum().reset_index()
        item_rev = item_rev.sort_values('Total Revenue', ascending=True)

        fig_item = px.bar(
            item_rev, y='Item Type', x='Total Revenue',
            orientation='h',
            text='Total Revenue',
            color='Total Revenue',
            color_continuous_scale='Blues'
        )
        fig_item.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_item.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=40, t=20, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_item, use_container_width=True)

    with col_p2:
        st.subheader("Profit Margin by Item Type")
        item_summary = df.groupby('Item Type').agg({
            'Total Revenue': 'sum',
            'Total Profit': 'sum',
            'Units Sold': 'sum'
        }).reset_index()
        item_summary['Margin %'] = (item_summary['Total Profit'] / item_summary['Total Revenue']) * 100
        item_summary = item_summary.sort_values('Margin %', ascending=False)

        fig_margin = px.bar(
            item_summary, x='Item Type', y='Margin %',
            color='Margin %',
            color_continuous_scale='Greens',
            text='Margin %'
        )
        fig_margin.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_margin.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=20, b=20),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_margin, use_container_width=True)

    st.subheader("Top Performing Product Summary")
    item_display = item_summary.copy()
    item_display['Total Revenue'] = item_display['Total Revenue'].map('${:,.2f}'.format)
    item_display['Total Profit'] = item_display['Total Profit'].map('${:,.2f}'.format)
    item_display['Units Sold'] = item_display['Units Sold'].map('{:,}'.format)
    item_display['Margin %'] = item_display['Margin %'].map('{:.1f}%'.format)
    st.dataframe(item_display, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 3: GEOGRAPHIC INTELLIGENCE
# ------------------------------------------
with tab_geography:
    st.subheader("Revenue by Region")
    region_df = df.groupby('Region')[['Total Revenue', 'Total Profit', 'Units Sold']].sum().reset_index()
    region_df = region_df.sort_values('Total Revenue', ascending=False)

    fig_region = px.bar(
        region_df, x='Region', y='Total Revenue',
        color='Region',
        text='Total Revenue'
    )
    fig_region.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_region.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_region, use_container_width=True)

    st.subheader("Top Countries by Profit")
    country_df = df.groupby(['Region', 'Country'])[['Total Revenue', 'Total Profit', 'Units Sold']].sum().reset_index()
    country_df = country_df.sort_values('Total Profit', ascending=False).head(10)
    
    country_display = country_df.copy()
    country_display['Total Revenue'] = country_display['Total Revenue'].map('${:,.2f}'.format)
    country_display['Total Profit'] = country_display['Total Profit'].map('${:,.2f}'.format)
    country_display['Units Sold'] = country_display['Units Sold'].map('{:,}'.format)
    st.dataframe(country_display, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 4: DATA EXPLORER & EXPORT
# ------------------------------------------
with tab_data:
    st.subheader("Explore Raw Dataset")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input("🔍 Quick Search by Country or Item Type", placeholder="e.g. Tuvalu, Clothes, Online")
    with col_s2:
        st.write("")
        st.write("")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv_data,
            file_name="filtered_kpi_sales_data.csv",
            mime="text/csv"
        )

    display_df = df.copy()
    if search_query:
        mask = (
            display_df['Country'].astype(str).str.contains(search_query, case=False, na=False) |
            display_df['Item Type'].astype(str).str.contains(search_query, case=False, na=False) |
            display_df['Sales Channel'].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[mask]

    st.dataframe(
        display_df[[
            'Order ID', 'Order Date', 'Region', 'Country', 'Item Type', 
            'Sales Channel', 'Units Sold', 'Total Revenue', 'Total Cost', 'Total Profit'
        ]],
        use_container_width=True,
        hide_index=True
    )
