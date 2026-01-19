from datetime import timedelta, datetime

from faker import Faker
import pandas as pd

fake = Faker()


def generate_customers(n):
    data = []
    for i in range(1, n + 1):
        data.append({
            "id": i,
            "email": fake.email(),
            "last_name": fake.last_name(),
            "first_name": fake.first_name(),
            "registration_date": fake.date_between(start_date="-3y", end_date="today")
        })

    return pd.DataFrame(data)


def generate_products(n):
    data = []
    categories = ["Backpack", "Wallet", "Handbag", "Shopper", "Belt bag"]
    for i in range(1, n + 1):
        data.append({
            "id": i,
            "sku": fake.uuid4()[:20],
            "name": fake.word().title(),
            "category": fake.random_element(categories),
            "price": fake.pyint(2, 500),
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
    dates[0] = fake.date_time_between(start_date="-3y")
    for s_idx in range(statuses.index(status)):
        dates[s_idx + 1] = dates[s_idx] + dt[s_idx]

    return dates


def generate_orders(n, products, customers=None):
    customer_ids = customers["id"].tolist() if customers is not None else []
    statuses = ["Pending", "Paid", "Shipped", "Delivered", "Canceled", "Returned"]
    order_data, order_items_data = [], []

    for i in range(1, n + 1):
        for j in range(fake.pyint(1, 5)):
            product = products.sample(1).iloc[0]
            order_items_data.append({
                "id": len(order_items_data) + 1,
                "order_id": i,
                "product_id": product["id"],
                "quantity": fake.pyint(1, 3),
                "unit_price": product["price"]
            })

        status = fake.random_element(statuses)
        dates = generate_dates(status, statuses)
        order_data.append({
            "id": i,
            "customer_id": fake.random_element(customer_ids) if customer_ids else None,
            "status": status,
            "order_date": dates[0],
            "payment_date": dates[1],
            "shipping_date": dates[2],
            "delivery_date": dates[3],
            "cancel_date": dates[4],
            "return_date": dates[5]
        })

    return pd.DataFrame(order_data), pd.DataFrame(order_items_data)
