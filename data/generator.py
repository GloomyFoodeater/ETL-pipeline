import os
from datetime import timedelta, datetime

from faker import Faker
import pandas as pd
from sqlalchemy import create_engine

from utils.console import print_centered

fake = Faker()


def generate_customers(n=500):
    data = []
    for i in range(1, n + 1):
        data.append({
            'customer_id': i,
            'customer_email': fake.email(),
            'customer_last_name': fake.last_name(),
            'customer_first_name': fake.first_name(),
            'customer_registration_date': fake.date_between(start_date='-2y', end_date='today')
        })

    return pd.DataFrame(data)


def generate_products(n=200):
    data = []
    categories = ['Backpack', 'Wallet', 'Handbag', 'Shopper', 'Belt bag']
    for i in range(1, n + 1):
        data.append({
            'id': i,
            'sku': fake.uuid4()[:20],
            'name': fake.word().title(),
            'category': fake.random_element(categories),
            'price': fake.pyint(2, 500),
        })
    return pd.DataFrame(data)


def generate_orders(customers, products, n=2000):
    customer_ids = customers['customer_id'].tolist()

    # Ordered for iteration to correctly assign status dates
    statuses = ['Pending', 'Paid', 'Shipped', 'Delivered', 'Canceled', 'Returned']

    order_data = []
    order_items_data = []
    for i in range(1, n + 1):
        for j in range(fake.pyint(1, 5)):
            product = products.sample(1).iloc[0]
            order_items_data.append({
                'order_item_id': len(order_items_data) + 1,
                'order_id': i,
                'order_item_product_sku': product['sku'],
                'order_item_quantity': fake.pyint(1, 3),
                'order_item_unit_price': product['price']
            })

        status = fake.random_element(statuses)
        dt = [
            timedelta(hours=fake.pyint(1, 3)),
            timedelta(days=fake.pyint(0, 3)),
            timedelta(days=fake.pyint(1, 3)),
            timedelta(hours=fake.pyint(1, 10)),
            timedelta(days=fake.pyint(1, 3))
        ]

        dates: list[datetime | None] = [None for _ in range(len(statuses))]
        dates[0] = fake.date_time_between(start_date='-1y')
        for s_idx in range(statuses.index(status)):
            dates[s_idx + 1] = dates[s_idx] + dt[s_idx]

        order_date, payment_date, shipping_date, delivery_date, cancel_date, return_date = dates

        order_data.append({
            'order_id': i,
            'customer_id': fake.random_element(customer_ids),
            'order_status': status,
            'order_date': order_date,
            'order_payment_date': payment_date,
            'order_shipping_date': shipping_date,
            'order_delivery_date': delivery_date,
            'order_cancel_date': cancel_date,
            'order_return_date': return_date,
        })

    return pd.DataFrame(order_data), pd.DataFrame(order_items_data)


if __name__ == '__main__':
    print_centered('Generating customers...')
    customers = generate_customers()
    print_centered('Generating products...')
    products = generate_products()
    print_centered('Generating orders...')
    orders, order_items = generate_orders(customers, products)

    folder = 'generated'
    os.makedirs(folder, exist_ok=True)
    print_centered('Connecting to database...')
    engine = create_engine('mysql://root:admin@127.0.0.1:3306/ecommerce_sample')

    print_centered('Writing customers...')
    customers.to_sql('customers', engine, if_exists='replace', index=False)
    print_centered('Writing products...')
    products.to_json(f'./{folder}/products.json', orient='records', indent=2, index=False)
    print_centered('Writing orders...')
    orders.to_sql('orders', engine, if_exists='replace', index=False)
    order_items.to_sql('order_items', engine, if_exists='replace', index=False)
    print_centered('Done!')
