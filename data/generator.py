# TODO: Change field names
from datetime import timedelta, datetime

from faker import Faker
import pandas as pd

fake = Faker()


def generate_customers(n=500):
    data = []
    for i in range(1, n + 1):
        data.append({
            'customer_id': i,
            'customer_email': fake.email(),
            'customer_last_name': fake.last_name(),
            'customer_first_name': fake.first_name(),
            'customer_registration_date': fake.date_between(start_date='-3y', end_date='today')
        })

    return pd.DataFrame(data)


def generate_products(n=200):
    data = []
    categories = ['Backpack', 'Wallet', 'Handbag', 'Shopper', 'Belt bag']
    for i in range(1, n + 1):
        data.append({
            'product_id': i,
            'product_sku': fake.uuid4()[:20],
            'product_name': fake.word().title(),
            'product_category': fake.random_element(categories),
            'product_price': fake.pyint(2, 500),
        })
    return pd.DataFrame(data)


def generate_dates(status, statuses):
    dt = [
        timedelta(hours=fake.pyint(1, 3)),
        timedelta(days=fake.pyint(0, 3)),
        timedelta(days=fake.pyint(1, 3)),
        timedelta(hours=fake.pyint(1, 10)),
        timedelta(days=fake.pyint(1, 3))
    ]

    dates: list[datetime | None] = [None for _ in range(len(statuses))]
    dates[0] = fake.date_time_between(start_date='-3y')
    for s_idx in range(statuses.index(status)):
        dates[s_idx + 1] = dates[s_idx] + dt[s_idx]

    return dates


def generate_orders(customers, products, n=2000):
    customer_ids = customers['customer_id'].tolist()
    statuses = ['Pending', 'Paid', 'Shipped', 'Delivered', 'Canceled', 'Returned']
    order_data, order_items_data = [], []

    for i in range(1, n + 1):
        for j in range(fake.pyint(1, 5)):
            product = products.sample(1).iloc[0]
            order_items_data.append({
                'order_item_id': len(order_items_data) + 1,
                'order_id': i,
                'product_id': product['product_id'],
                'order_item_quantity': fake.pyint(1, 3),
                'order_item_unit_price': product['product_price']
            })

        status = fake.random_element(statuses)
        dates = generate_dates(status, statuses)
        order_data.append({
            'order_id': i,
            'customer_id': fake.random_element(customer_ids),
            'order_status': status,
            'order_date': dates[0],
            'order_payment_date': dates[1],
            'order_shipping_date': dates[2],
            'order_delivery_date': dates[3],
            'order_cancel_date': dates[4],
            'order_return_date': dates[5]
        })

    return pd.DataFrame(order_data), pd.DataFrame(order_items_data)


def generate():
    customers = generate_customers(500)
    products = generate_products(200)
    orders, order_items = generate_orders(customers, products, 2000)

    return customers, products, orders, order_items
