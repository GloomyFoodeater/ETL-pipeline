import yaml
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

from generator import generate_customers, generate_products, generate_orders

if __name__ == "__main__":
    customers = generate_customers(500)
    products = generate_products(200)
    orders, order_items = generate_orders(500, products, customers)

    customers = customers.add_prefix("customer_")
    products = products.add_prefix("product_")
    orders = (orders
              .add_prefix("order_")
              .rename(columns={"order_customer_id": "customer_id", "order_order_date": "order_date"}))
    order_items = (order_items
                   .add_prefix("order_item_")
                   .rename(columns={"order_item_order_id": "order_id", "order_item_product_id": "product_id"}))

    with open("../config.yaml", "r") as f:
        config = yaml.safe_load(f)
    print("Connecting to database...")
    engine = create_engine(config["sql_source_url"])
    if database_exists(engine.url):
        drop_database(engine.url)
    create_database(engine.url)

    print("Writing customers...")
    customers.to_sql("customers", engine, if_exists="replace", index=False)
    print("Writing products...")
    products.to_sql("products", engine, if_exists="replace", index=False)
    print("Writing orders...")
    orders.to_sql("orders", engine, if_exists="replace", index=False)
    order_items.to_sql("order_items", engine, if_exists="replace", index=False)

    print("Done!")
