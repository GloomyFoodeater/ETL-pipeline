import math
import streamlit as st


class Paginator:
    def __init__(self, container, prefix):
        self.prefix = prefix
        self.container = container
        self.items_per_page = st.session_state.get(prefix + 'ipp', 10)
        self.total_pages = max(math.ceil(len(container) / self.items_per_page), 1)
        self.page_number = st.session_state.get(prefix + 'pn', 1)
        if self.page_number > self.total_pages:
            self.page_number = 1

    def get_page(self):
        start = (self.page_number - 1) * self.items_per_page
        end = start + self.items_per_page

        return self.container[start:end]

    def write(self):
        label_col, page_col, items_col = st.columns([3, 1, 1])
        label_col.write(f'Page {self.page_number} of {self.total_pages}')
        page_col.number_input(
            'Page',
            min_value=1,
            max_value=self.total_pages,
            value=self.page_number,
            step=1,
            key=self.prefix + 'pn'
        )
        items_col.number_input(
            'Items per page',
            min_value=1,
            value=self.items_per_page,
            key=self.prefix + 'ipp'
        )
