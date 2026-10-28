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
