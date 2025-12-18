import streamlit as st

import altair as alt
import yaml

from utils.collections import reverse_map
from .paginator import Paginator
from .sort_widget import write_sort_widget


def write_customer_section(connection):
    st.header('RFM metrics')

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    segment_map = config['segment_map']
    segments = [None, 'Unclassified'] + list(segment_map.keys())
    segment = st.selectbox('Select segment', segments)

    sort_by, order_by = write_sort_widget('customer', {
        'Recency': 'recency',
        'Monetary': 'monetary',
        'Frequency': 'frequency'
    })

    if sort_by == 'recency':
        sort_by = f'recency IS NULL {order_by}, recency '

    sql_query = f'''
    SELECT rfm_code, CONCAT(first_name, ' ', last_name) name, email, recency, frequency, monetary
    FROM dim_customer
    ORDER BY {sort_by} {order_by}
    '''
    customers = connection.query(sql_query)

    code_to_segment = reverse_map(segment_map)
    customers['segment'] = (customers['rfm_code']
                            .map(code_to_segment)
                            .fillna('Unclassified'))
    customers['monetary'] /= 100
    segment_counts = (customers['segment']
                      .value_counts()
                      .reindex(segments[1:], fill_value=0)
                      .reset_index())
    if segment:
        customers = customers[customers['segment'] == segment]

    customer_paginator = Paginator(customers, 'customer')
    config = {
        'name': st.column_config.TextColumn('Name'),
        'recency': st.column_config.NumberColumn('R', format='%s days'),
        'frequency': st.column_config.NumberColumn('F', format='%s Orders'),
        'monetary': st.column_config.NumberColumn('M', format='%s BYN'),
        'segment': st.column_config.TextColumn('Segment')
    }
    st.dataframe(customer_paginator.get_page(), column_config=config, hide_index=True)
    customer_paginator.write()

    chart = alt.Chart(segment_counts).mark_arc().encode(
        theta=alt.Theta('count:Q', title='Counter'),
        color=alt.Color('segment:N', title='Segment', scale=alt.Scale(scheme='category20'))
    ).properties(title='Segment distribution')
    st.altair_chart(chart)
