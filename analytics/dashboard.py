import os

import streamlit as st

from widgets.divider import write_divider
from widgets.customers_section import write_customer_section
from widgets.sales_section import write_sales_section
from widgets.products_section import write_product_section

if __name__ == '__main__':
    if os.getenv("env") == "dev":
        if st.button('🔄 Reload'):
            st.cache_data.clear()
            st.rerun()

    conn = st.connection('data_warehouse', type='sql')

    st.set_page_config(page_title='Analytics Dashboard')

    write_sales_section(conn)

    write_divider()

    write_product_section(conn)

    write_divider()

    write_customer_section(conn)
