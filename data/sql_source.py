import yaml
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

from generator import generate

if __name__ == '__main__':
    customers, products, orders, order_items = generate()

    with open('../config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('Connecting to database...')
    engine = create_engine(config['sql_source_url'])
    if database_exists(engine.url):
        drop_database(engine.url)
    create_database(engine.url)

    print('Writing customers...')
    customers.to_sql('customers', engine, if_exists='replace', index=False)
    print('Writing products...')
    products.to_sql('products', engine, if_exists='replace', index=False)
    print('Writing orders...')
    orders.to_sql('orders', engine, if_exists='replace', index=False)
    order_items.to_sql('order_items', engine, if_exists='replace', index=False)

    print('Done!')
