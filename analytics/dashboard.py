# TODO: Output data frames without sorting
from datetime import date

import pandas as pd
import streamlit as st
import altair as alt

from paginator import Paginator

conn = st.connection('data_warehouse', type='sql')


def write_turnover_and_sales():
    st.header('Turnover and sales')
    left, right = st.columns(2)
    today = date.today()
    start_date = left.date_input('Start date', date(today.year - 1, today.month, today.day))
    end_date = right.date_input('End date', today)

    if start_date > end_date:
        st.error('❌ Start date must be before or equal to end date')
        return

    query_params = {'start_date': start_date, 'end_date': end_date}
    sql_query = '''
        SELECT COALESCE(SUM(fo.total_price), 0) turnover, COUNT(fo.id) sales_count
        FROM fact_order fo
        JOIN dim_date dt ON fo.created_at_id = dt.id
        WHERE dt.full_date BETWEEN :start_date AND :end_date
    '''
    turnover, sales_count = conn.query(sql_query, params=query_params).loc[0, ['turnover', 'sales_count']]
    turnover /= 100
    sql_query = '''
    SELECT dt.year, dt.month, COALESCE(SUM(fo.total_price), 0) AS turnover, COUNT(fo.id) AS sales_count
    FROM fact_order fo
    JOIN dim_date dt ON fo.created_at_id = dt.id
    WHERE dt.full_date BETWEEN :start_date AND :end_date
    GROUP BY dt.year, dt.month
    ORDER BY dt.year, dt.month
    '''
    df = conn.query(sql_query, params=query_params)
    df['turnover'] /= 100

    all_dates = pd.date_range(start=start_date, end=end_date, freq='MS')

    calendar = pd.DataFrame({
        'year': all_dates.year,
        'month': all_dates.month,
        'period': all_dates.strftime('%b %Y')
    })

    df = calendar.merge(df, on=['year', 'month'], how='left')
    df.fillna({'turnover': 0, 'sales_count': 0}, inplace=True)

    turnover_col, sales_col = st.columns(2)
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('period', title='Month', sort=all_dates),
        y=alt.Y('turnover', title='Turnover')
    ).properties(title='Turnover by months')
    turnover_col.text(f'Turnover: {turnover} BYN')
    turnover_col.altair_chart(chart)
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('period', title='Month', sort=all_dates),
        y=alt.Y('sales_count', title='Sales')
    ).properties(title='Sales by months')
    sales_col.text(f'Sales count: {sales_count}')
    sales_col.altair_chart(chart)


def write_top_products():
    st.header('Top products')

    categories = [None, 'Backpack', 'Wallet', 'Handbag', 'Shopper', 'Belt bag', 'Trinket']
    category = st.selectbox('Choose a category', categories)
    left, right = st.columns(2)
    sort_by = left.selectbox('Sort by', ['Turnover', 'Sales count'])
    if sort_by == 'Turnover':
        sort_by = 'turnover'
    elif sort_by == 'Sales count':
        sort_by = 'sales_count'
    order_by = right.selectbox('Order by', ['DESC', 'ASC'])

    sql_query = f'''
    SELECT  name, sku, category, price, turnover, sales_count 
    FROM    dim_product
    {f"WHERE p.category = '{category}'" if category else ''}
    ORDER BY {sort_by} {order_by}
    '''
    top_products = conn.query(sql_query)
    top_products['turnover'] /= 100

    product_paginator = Paginator(top_products, 'product')

    config = {
        'name': st.column_config.TextColumn('Product'),
        'sku': st.column_config.TextColumn('SKU'),
        'category': st.column_config.TextColumn('Category'),
        'price': st.column_config.NumberColumn('Price', format='%s USD'),
        'sales_count': st.column_config.NumberColumn('Sales count'),
        'turnover': st.column_config.NumberColumn('Turnover', format='%s USD'),
    }
    st.dataframe(product_paginator.get_page(), column_config=config, hide_index=True)

    product_paginator.write()


def write_rfm_metrics():
    st.header('RFM metrics')
    segments = [
        None,
        'Champions',
        'Loyal Customers',
        'Potential Loyalists',
        'New Customers',
        'Promising',
        'Need Attention',
        'About to Sleep',
        'Cannot Lose Them',
        'At Risk',
        'Hibernating',
        'Lost Customers',
        'Potential Customers'
    ]

    sql_query = '''
    SELECT  segment, CONCAT(first_name, ' ', last_name) name, email, recency, frequency, monetary
    FROM dim_customer
    '''
    customers = conn.query(sql_query)
    customers['monetary'] /= 100
    segment_counts = (customers['segment']
                      .value_counts()
                      .reindex(segments[1:], fill_value=0)
                      .reset_index())
    segment = st.selectbox('Select segment', segments)
    if segment:
        customers = customers[customers['segment'] == segment]

    config = {
        'name': st.column_config.TextColumn('Name'),
        'recency': st.column_config.NumberColumn('R', format='%s days'),
        'frequency': st.column_config.NumberColumn('F', format='%s Orders'),
        'monetary': st.column_config.NumberColumn('M', format='%s BYN'),
        'segment': st.column_config.TextColumn('Segment')
    }

    customer_paginator = Paginator(customers, 'customer')

    st.dataframe(customer_paginator.get_page(), column_config=config, hide_index=True)

    customer_paginator.write()

    chart = alt.Chart(segment_counts).mark_arc().encode(
        theta=alt.Theta('count:Q', title='Counter'),
        color=alt.Color('segment:N', title='Segment', scale=alt.Scale(scheme='category20'))
    ).properties(title='Segment distribution')
    st.altair_chart(chart)


def write_divider():
    st.markdown('<hr>', unsafe_allow_html=True)


if __name__ == '__main__':
    st.set_page_config(page_title='Analytics Dashboard')

    write_turnover_and_sales()

    write_divider()

    write_top_products()

    write_divider()

    write_rfm_metrics()
