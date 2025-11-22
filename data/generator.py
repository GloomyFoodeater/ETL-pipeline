import os
from datetime import datetime

from faker import Faker
import pandas as pd
import random

fake = Faker()

# -----------------------------
# Customers (с невалидными email'ами)
# -----------------------------
def generate_customers(n=500):
    customers = []
    for i in range(1, n+1):
        email = fake.email()
        # ~3% невалидных email'ов
        if random.random() < 0.03:
            email = "invalid_email_" + str(i)
        customers.append({
            "customer_id": i,
            "name": fake.name(),
            "email": email,
            "country": fake.country(),
            "registration_date": fake.date_between(start_date="-2y", end_date="today")
        })

    # Добавляем дубликаты (5%)
    for i in range(int(n * 0.05)):
        customers.append(customers[random.randint(0, n-1)])

    return pd.DataFrame(customers)


# -----------------------------
# Products (с отсутствующими ценами)
# -----------------------------
def generate_products(n=200):
    categories = ["Shoes", "Electronics", "Books", "Clothing", "Home"]
    products = []
    for i in range(1, n+1):
        # ~5% продуктов без цены
        if random.random() < 0.05:
            price = None
        else:
            price = round(random.uniform(5, 500), 2)

        products.append({
            "product_id": i,
            "name": fake.word().title(),
            "category": random.choice(categories),
            "brand": fake.company(),
            "price": price,
            "currency": "USD"
        })
    return pd.DataFrame(products)


# -----------------------------
# Orders + Order Items (с пустыми заказами)
# -----------------------------
def generate_orders(customers, products, n=2000):
    orders = []
    order_items = []
    for i in range(1, n+1):
        cust_id = random.choice(customers["customer_id"].tolist())
        order_date = fake.date_between(start_date="-1y", end_date="today")
        status = random.choice(["Completed", "Cancelled", "Returned"])
        order_total = 0
        order_id = i

        # Заказ без позиций (2%)
        if random.random() < 0.02:
            orders.append({
                "order_id": order_id,
                "customer_id": cust_id,
                "order_date": order_date,
                "status": status,
                "total_amount": 0,
                "currency": "USD"
            })
            continue

        for j in range(random.randint(1, 5)):
            product = products.sample(1).iloc[0]
            qty = random.randint(1, 3)
            unit_price = product["price"] if product["price"] else 0
            order_total += qty * unit_price

            order_items.append({
                "order_item_id": f"{i}-{j}",
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": qty,
                "unit_price": unit_price
            })

        orders.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "order_date": order_date,
            "status": status,
            "total_amount": round(order_total, 2),
            "currency": "USD"
        })

    return pd.DataFrame(orders), pd.DataFrame(order_items)


# -----------------------------
# Transactions (camelCase + отрицательные суммы)
# -----------------------------
def generate_transactions(orders):
    transactions = []
    for _, order in orders.iterrows():
        if order["status"] == "Completed":
            amount = order["total_amount"]
            # Отрицательные суммы (1%)
            if random.random() < 0.01:
                amount = -abs(amount)

            transactions.append({
                "transactionId": f"T{order['order_id']}",
                "orderId": order["order_id"],
                "paymentMethod": random.choice(["Card", "PayPal", "BankTransfer"]),
                "paymentDate": order["order_date"],
                "amount": amount,
                "currency": order["currency"]
            })
    return pd.DataFrame(transactions)


# -----------------------------
# Reviews (с некорректными датами)
# -----------------------------
def generate_reviews(orders, products, n=1000):
    reviews = []
    for i in range(1, n+1):
        order = orders.sample(1).iloc[0]
        product = products.sample(1).iloc[0]
        # Некорректные даты (2%)
        if random.random() < 0.02:
            review_date = "32-13-2025"
        else:
            review_date = fake.date_between(start_date=order["order_date"], end_date="today")

        reviews.append({
            "review_id": i,
            "order_id": order["order_id"],
            "product_id": product["product_id"],
            "customer_id": order["customer_id"],
            "rating": random.randint(1, 5),
            "comment": fake.sentence(),
            "review_date": review_date
        })
    return pd.DataFrame(reviews)


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    customers = generate_customers()
    products = generate_products()
    orders, order_items = generate_orders(customers, products)
    transactions = generate_transactions(orders)
    reviews = generate_reviews(orders, products)

    folder = "generated_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(folder, exist_ok=True)

    customers.to_csv(f"./{folder}/customers.csv", index=False)
    products.to_csv(f"./{folder}/products.csv", index=False)
    orders.to_csv(f"./{folder}/orders.csv", index=False)
    order_items.to_csv(f"./{folder}/order_items.csv", index=False)
    transactions.to_csv(f"./{folder}/transactions.csv", index=False)
    reviews.to_csv(f"./{folder}/reviews.csv", index=False)

    print("✅ Данные сгенерированы с дополнительными ошибками (дубликаты, пустые заказы, продукты без цены, невалидные email'ы, camelCase транзакции, отрицательные суммы, некорректные даты)")
