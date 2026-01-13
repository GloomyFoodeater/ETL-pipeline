from typing import List

import pandas as pd

from models.CustomerModel import CustomerModel
from models.ProductModel import ProductModel
from models.OrderModel import OrderModel

from generator import generate

from fastapi import FastAPI

customers, products, orders, order_items = [df.replace({pd.NaT: None}).to_dict(orient="records") for df in generate()]
orders = [
    {**order, "items": [{
        "product_id": item["product_id"],
        "order_item_quantity": item["order_item_quantity"],
        "order_item_unit_price": item["order_item_unit_price"]
    } for item in order_items if item["order_id"] == order["order_id"]]}
    for order in orders
]

app = FastAPI()


@app.get("/customers", response_model=List[CustomerModel])
async def get_customers():
    return customers


@app.get("/products", response_model=List[ProductModel])
async def get_products():
    return products


@app.get("/orders", response_model=List[OrderModel])
async def get_orders():
    return orders
