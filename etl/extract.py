import pandas as pd
import yaml
from sqlalchemy import create_engine

# TODO: Fix config file paths
def extract_sql_source():
    with open("../config.yaml", "r") as f:
        config = yaml.safe_load(f)

        print("[sql_source] Connecting to database...")
        engine = create_engine(config["sql_source_url"])

        print("[sql_source] Extracting customers...")
        customers = pd.read_sql("customers", engine)
        print("[sql_source] Extracting products...")
        products = pd.read_sql("products", engine)
        print("[sql_source] Extracting orders...")
        orders = pd.read_sql("orders", engine)
        order_items = pd.read_sql("order_items", engine)

        return {
            "customer": customers,
            "product": products,
            "order": orders,
            "order_item": order_items
        }


def extract_api_source():
    with open("../config.yaml", "r") as f:
        config = yaml.safe_load(f)

        print("[api_source] Extracting products...")
        products = pd.read_json(config["api_source_url"] + "/products")

        print("[api_source] Extracting orders...")
        orders = pd.read_json(config["api_source_url"] + "/orders")

        return {
            "product": products,
            "order": orders
        }
