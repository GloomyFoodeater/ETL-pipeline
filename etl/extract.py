import pandas as pd
import yaml
from sqlalchemy import create_engine


def extract() -> dict[str, pd.DataFrame]:
    with open('./../config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    print('Connecting to database...')
    engine = create_engine(config['sql_source_url'])

    print('Extracting customers...')
    customers = pd.read_sql('customers', engine)
    print('Extracting products...')
    products = pd.read_sql('products', engine)
    print('Extracting orders...')
    orders = pd.read_sql('orders', engine)
    order_items = pd.read_sql('order_items', engine)

    return {
        'dim_customer': customers,
        'dim_product': products,
        'fact_order': orders,
        'fact_order_item': order_items
    }
