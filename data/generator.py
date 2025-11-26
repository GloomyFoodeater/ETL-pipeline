import os

from faker import Faker
import pandas as pd
import random
from random import random, choice, uniform, randint
from sqlalchemy import create_engine

fake = Faker()


def generate_customers(n=500, dup_rate=0.05, invalid_email_rate=0.03):
    """Generate customers with duplicates and invalid emails in pascal case."""
    unique_n = int((1 - dup_rate) * n)

    customers = []
    for i in range(1, unique_n + 1):
        email = fake.email()
        # Make email invalid
        if random() < invalid_email_rate:
            email = "invalid_email_" + str(i)
        customers.append({
            "CustomerId": i,
            "CustomerName": fake.name(),
            "CustomerEmail": email,
            "CustomerCountry": fake.country(),
            "CustomerRegistrationDate": fake.date_between(start_date="-2y", end_date="today")
        })

    # Add duplicates
    for i in range(unique_n + 1, n + 1):
        customers.append(customers[randint(0, unique_n)])

    return pd.DataFrame(customers)


def generate_products(currencies, categories, n=200, priceless_rate=0.05, category_error_rate=0.03):
    """Generate products with priceless instances and category errors in camel case."""

    products = []
    for i in range(1, n + 1):

        # Remove price
        if random() < priceless_rate:
            price = None
        else:
            price = round(uniform(5, 500), 2)

        # Lowercase category
        category = choice(categories)
        if random() < category_error_rate:
            category = category.lower()

        products.append({
            "productId": i,
            "productName": fake.word().title(),
            "productCategory": category,
            "productBrand": fake.company(),
            "productPrice": price,
            "productCurrency": choice(currencies)
        })
    return pd.DataFrame(products)


def generate_orders(customers, products, currencies, n=2000, empty_orders=0.02, wild_pointer_rate=0.02):
    """Generate orders and order items with empty orders and wild pointers to customers."""
    customer_ids = customers["CustomerId"].tolist()

    orders = []
    order_items = []
    for i in range(1, n + 1):
        # Generate wild pointers to customers
        customer_id = (max(customer_ids) + 1) if random() < wild_pointer_rate else choice(customer_ids)
        order_date = fake.date_between(start_date="-1y", end_date="today")
        status = choice(["Completed", "Cancelled", "Returned"])
        order_id = i

        # Generate non-empty orders
        if random() >= empty_orders:
            for j in range(randint(1, 5)):
                product = products.sample(1).iloc[0]
                qty = randint(1, 3)
                unit_price = product["productPrice"] or 0

                order_items.append({
                    "OrderItemId": j,
                    "OrderId": order_id,
                    "ProductId": product["productId"],
                    "OrderItemQuantity": qty,
                    "OrderItemUnitPrice": unit_price
                })

        orders.append({
            "OrderId": order_id,
            "CustomerId": customer_id,
            "OrderDate": order_date,
            "OrderStatus": status,
            "OrderCurrency": choice(currencies)
        })

    return pd.DataFrame(orders), pd.DataFrame(order_items)


def generate_transactions(orders, order_items, payment_methods, order_rate=0.1, invalid_amount=0.01):
    """Generate transactions by orders with unfinished orders and invalid amounts in prefixless camel case."""
    transactions = []

    for _, order in orders.iterrows():
        # Can be unfinished order
        if random() < order_rate:
            items = order_items[order_items["OrderId"] == order["OrderId"]]
            amount = (items["OrderItemQuantity"] * items["OrderItemUnitPrice"]).sum()

            # Generate invalid amount
            if random() < invalid_amount:
                amount = -abs(amount)

            transactions.append({
                "id": f"T{order['OrderId']}",
                "orderId": order["OrderId"],
                "paymentMethod": choice(payment_methods),
                "paymentDate": order["OrderDate"],
                "amount": amount,
                "currency": order["OrderCurrency"]
            })
    return pd.DataFrame(transactions)


if __name__ == "__main__":
    currencies = ['USD', 'EUR', 'BYN']
    categories = ["Shoes", "Electronics", "Books", "Clothing", "Home"]
    payment_methods = ["Card", "PayPal", "BankTransfer"]

    print('Generating customers...')
    customers = generate_customers()
    print('Generating products...')
    products = generate_products(currencies, categories)
    print('Generating orders...')
    orders, order_items = generate_orders(customers, products, currencies)
    print('Generating transactions...')
    transactions = generate_transactions(orders, order_items, payment_methods)

    folder = "generated"
    os.makedirs(folder, exist_ok=True)
    print('Connecting to database...')
    engine = create_engine('mysql://root:admin@127.0.0.1:3306/ecommerce_sample')

    print('Writing customers...')
    customers.to_sql('customers', engine, if_exists='replace', index=False)
    print('Writing products...')
    products.to_json(f"./{folder}/products.json", orient="records", indent=2, index=False)
    print('Writing orders...')
    orders.to_sql('orders', engine, if_exists='replace', index=False)
    order_items.to_sql('order_items', engine, if_exists='replace', index=False)
    print('Writing transactions...')
    transactions.to_csv(f"./{folder}/transactions.csv", index=False)
    print('Done!')
