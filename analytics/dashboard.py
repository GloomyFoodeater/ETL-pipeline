from datetime import date

import pandas as pd
import streamlit as st
import altair as alt

conn = st.connection('data_warehouse', type='sql')


def write_turnover_and_sales():
    st.header('Turnover and sales')
    left, right = st.columns(2)
    today = date.today()
    start_date = left.date_input('Start date', date(today.year - 1, today.month, today.day))
    end_date = right.date_input('End date', today)

    turnover_col, sales_col = st.columns(2)
    if start_date < end_date:
        with turnover_col:
            script = f'''
                SELECT SUM(fo.total_price) turnover
                FROM fact_order fo
                JOIN dim_date dt ON fo.created_at = dt.id
                WHERE dt.full_date BETWEEN '{start_date}' AND '{end_date}'
            '''
            turnover = conn.query(script)['turnover'].iloc[0] or 0
            st.text(f'Turnover: {turnover}')

            script = f'''
            SELECT 
                dt.year,
                dt.month,
                SUM(fo.total_price) AS turnover
            FROM fact_order fo
            JOIN dim_date dt ON fo.created_at = dt.id
            WHERE dt.full_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY dt.year, dt.month
            ORDER BY dt.year, dt.month;
            '''
            turnover_by_months = conn.query(script)
            turnover_by_months['year_month'] = pd.to_datetime(turnover_by_months[['year', 'month']].assign(day=1))

            chart = alt.Chart(turnover_by_months).mark_bar(size=10).encode(
                x=alt.X('year_month:T', axis=alt.Axis(format='%b %Y', title='Month', labelAngle=-90)),
                y=alt.Y('turnover:Q', title='Turnover')
            )

            st.altair_chart(chart)
        with sales_col:
            script = f'''
                SELECT COUNT(fo.id) sales_count
                FROM fact_order fo
                JOIN dim_date dt ON fo.created_at = dt.id
                WHERE dt.full_date BETWEEN '{start_date}' AND '{end_date}'
            '''
            sales_count = conn.query(script)['sales_count'].iloc[0]
            st.text(f'Sales count: {sales_count}')

            script = f'''
            SELECT 
                dt.year,
                dt.month,
                COUNT(fo.id) AS sales_count
            FROM fact_order fo
            JOIN dim_date dt ON fo.created_at = dt.id
            WHERE dt.full_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY dt.year, dt.month
            ORDER BY dt.year, dt.month;
            '''
            orders_by_months = conn.query(script)
            orders_by_months['year_month'] = pd.to_datetime(turnover_by_months[['year', 'month']].assign(day=1))

            chart = alt.Chart(orders_by_months).mark_bar(size=10).encode(
                x=alt.X('year_month:T', axis=alt.Axis(format='%b %Y', title='Month', labelAngle=-90)),
                y=alt.Y('sales_count:Q', title='Sales count')
            )

            st.altair_chart(chart)
    else:
        st.error('❌ Start date must be before or equal to end date')


def write_top_products():
    st.header('Top products')

    categories = [None, 'Backpack', 'Wallet', 'Handbag', 'Shopper', 'Belt bag', 'Trinket']
    limit = st.number_input('Top products limit', min_value=0)
    category = st.selectbox('Choose a category', categories)
    left, right = st.columns(2)
    sort_by = left.selectbox('Sort by', ['Turnover', 'Sales count'])
    if sort_by == 'Turnover':
        sort_by = 'turnover'
    elif sort_by == 'Sales count':
        sort_by = 'sales_count'
    order_by = right.selectbox('Order by', ['DESC', 'ASC'])

    script = f'''
    SELECT p.name, p.sku, p.category, t.turnover, t.sales_count FROM
    	(SELECT oi.product_id, SUM(oi.quantity * oi.unit_price) turnover, SUM(oi.quantity) sales_count
    	FROM fact_order_item oi
    	GROUP BY oi.product_id) t
    JOIN dim_product p ON p.id = t.product_id
    {f"WHERE p.category = '{category}'" if category else ''}
    ORDER BY t.{sort_by} {order_by}
    {f"LIMIT {limit}" if limit else ''}
    '''
    top_products = conn.query(script)

    config = {
        'name': st.column_config.TextColumn('Product'),
        'sku': st.column_config.TextColumn('SKU'),
        'sales_count': st.column_config.NumberColumn('Sales count'),
        'turnover': st.column_config.NumberColumn('Turnover', format='%s BYN'),
    }
    st.dataframe(top_products, column_config=config, hide_index=True)


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
        'Others'
    ]

    script = '''
    WITH rfm_scores AS (
            SELECT
                customer_id,
                recency,
                frequency,
                monetary,
                NTILE(5) OVER (ORDER BY recency ASC) AS r_score,
                NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
                NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
    FROM customer_rfm)
    SELECT
            CASE
                WHEN CONCAT(r_score, f_score, m_score) IN ('555','554','544','545','454','455','445') 
                    THEN 'Champions'
                WHEN CONCAT(r_score, f_score, m_score) IN ('543','444','435','355','354','345','344','335') 
                    THEN 'Loyal Customers'
                WHEN CONCAT(r_score, f_score, m_score) IN ('553','551','552','541','542','533','532','531',
                                                           '452','451','442','441','431','453','433','432',
                                                           '423','353','352','351','342','341','333','323') 
                    THEN 'Potential Loyalists'
                WHEN CONCAT(r_score, f_score, m_score) IN ('512','511','422','421','412','411','311') 
                    THEN 'New Customers'
                WHEN CONCAT(r_score, f_score, m_score) IN ('525','524','523','522','521','515','514','513',
                                                           '425','424','413','414','415','315','314','313') 
                    THEN 'Promising'
                WHEN CONCAT(r_score, f_score, m_score) IN ('535','534','443','434','343','334','325','324') 
                    THEN 'Need Attention'
                WHEN CONCAT(r_score, f_score, m_score) IN ('331','321','312','221','213','231','241','251') 
                    THEN 'About to Sleep'
                WHEN CONCAT(r_score, f_score, m_score) IN ('155','154','144','214','215','115','114','113') 
                    THEN 'Cannot Lose Them'
                WHEN CONCAT(r_score, f_score, m_score) IN ('255','254','245','244','253','252','243','242',
                                                           '235','234','225','224','153','152','145','143',
                                                           '142','135','134','133','125','124') 
                    THEN 'At Risk'
                WHEN CONCAT(r_score, f_score, m_score) IN ('332','322','233','232','223','222','132','123',
                                                           '122','212','211') 
                    THEN 'Hibernating'
                WHEN CONCAT(r_score, f_score, m_score) IN ('111','112','121','131','141','151') 
                    THEN 'Lost Customers'
                ELSE 'Others'
            END AS segment,
            CONCAT(first_name, ' ', last_name) name,
            email,
            recency,
            frequency,
            monetary
        FROM rfm_scores
        JOIN dim_customer ON dim_customer.id = rfm_scores.customer_id;
    '''
    rfm = conn.query(script)
    segment_counts = (rfm['segment']
                      .value_counts()
                      .reindex(segments[1:], fill_value=0)
                      .reset_index())

    config = {
        'name': st.column_config.TextColumn('Name'),
        'recency': st.column_config.NumberColumn('R', format='%s days'),
        'frequency': st.column_config.NumberColumn('F', format='%s Orders'),
        'monetary': st.column_config.NumberColumn('M', format='%s BYN'),
        'segment': st.column_config.TextColumn('Segment')
    }

    segment = st.selectbox('Select segment', segments)
    if segment:
        rfm = rfm[rfm['segment'] == segment]
    st.dataframe(rfm, column_config=config, hide_index=True)

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
