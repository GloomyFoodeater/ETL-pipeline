import streamlit as st


def write_sort_widget(prefix, option_map):
    left, right = st.columns(2)
    sort_by = left.selectbox('Sort by', option_map.keys(), key=f'{prefix}_sb')
    sort_by = option_map.get(sort_by)
    order_by = right.selectbox('Order by', ['DESC', 'ASC'], key=f'{prefix}_ob')
    return sort_by, order_by
