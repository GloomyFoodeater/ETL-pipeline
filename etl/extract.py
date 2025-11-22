import pandas as pd
from sqlalchemy import create_engine

from utils.console import print_centered


def extract() -> dict[str, pd.DataFrame]:
    folder = "./../data/generated"
    print_centered('Connecting to database...')
    engine = create_engine('mysql://root:admin@127.0.0.1:3306/ecommerce_sample')

    print('Extracting customers...')
    customers = pd.read_sql('customers', engine)
    print('Extracting products...')
    products = pd.read_json(f"{folder}/products.json")
    print('Extracting orders...')
    orders = pd.read_sql('orders', engine)
    order_items = pd.read_sql('order_items', engine)
    print('Extracting transactions...')
    transactions = pd.read_csv(f"{folder}/transactions.csv")
    print('Done!')

    return {
        'customers': customers,
        'products': products,
        'orders': orders,
        'order_items': order_items,
        'transactions': transactions
    }
