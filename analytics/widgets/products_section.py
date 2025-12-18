import streamlit as st

from .paginator import Paginator
from .sort_widget import write_sort_widget


def write_product_section(connection):
    st.header('Top products')

    sql_query = 'SELECT DISTINCT category FROM dim_product ORDER BY category'
    categories = [None] + connection.query(sql_query).dropna()['category'].tolist()
    category = st.selectbox('Choose a category', categories)

    sort_by, order_by = write_sort_widget('product', {
        'Turnover': 'turnover',
        'Sales count': 'sales_count'
    })

    sql_query = f'''
    SELECT  name, sku, category, price, turnover, sales_count 
    FROM    dim_product
    {f"WHERE category = '{category}'" if category else ''}
    ORDER BY {sort_by} {order_by}
    '''
    top_products = connection.query(sql_query)
    top_products['price'] /= 100
    top_products['turnover'] /= 100

    product_paginator = Paginator(top_products, 'product')
    config = {
        'name': st.column_config.TextColumn('Product'),
        'sku': st.column_config.TextColumn('SKU'),
        'category': st.column_config.TextColumn('Category'),
        'price': st.column_config.NumberColumn('Price', format='%s BYN'),
        'sales_count': st.column_config.NumberColumn('Sales count'),
        'turnover': st.column_config.NumberColumn('Turnover', format='%s BYN'),
    }
    st.dataframe(product_paginator.get_page(), column_config=config, hide_index=True)
    product_paginator.write()
