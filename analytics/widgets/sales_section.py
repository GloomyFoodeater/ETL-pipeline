from datetime import date

import pandas as pd
import streamlit as st
import altair as alt


def write_sales_section(connection):
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
    turnover, sales_count = connection.query(sql_query, params=query_params).loc[0, ['turnover', 'sales_count']]
    turnover /= 100
    sql_query = '''
    SELECT dt.year, dt.month, COALESCE(SUM(fo.total_price), 0) AS turnover, COUNT(fo.id) AS sales_count
    FROM fact_order fo
    JOIN dim_date dt ON fo.created_at_id = dt.id
    WHERE dt.full_date BETWEEN :start_date AND :end_date
    GROUP BY dt.year, dt.month
    ORDER BY dt.year, dt.month
    '''
    df = connection.query(sql_query, params=query_params)
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
