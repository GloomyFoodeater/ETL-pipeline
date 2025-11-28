import pandas as pd
from sqlalchemy import create_engine

from utils.console import print_centered


def extract() -> dict[str, pd.DataFrame]:
    folder = "./../data/generated"
    print_centered('Connecting to database...')
    engine = create_engine('mysql://root:admin@127.0.0.1:3306/ecommerce_sample')

    print_centered('Extracting customers...')
    customers = pd.read_sql('customers', engine)
    print_centered('Extracting products...')
    products = pd.read_json(f"{folder}/products.json")
    print_centered('Extracting orders...')
    orders = pd.read_sql('orders', engine)
    order_items = pd.read_sql('order_items', engine)
    print_centered('Done!')

    return {
        'dim_customer': customers,
        'dim_product': products,
        'fact_order': orders,
        'fact_order_item': order_items
    }
