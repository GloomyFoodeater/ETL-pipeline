from typing import List

import uvicorn
import pandas as pd

from generator import generate_products, generate_orders
from models.ProductModel import ProductModel
from models.OrderModel import OrderModel

from fastapi import FastAPI

def get_data():
    products = generate_products(100)
    orders, order_items = generate_orders(500, products)
    orders.replace({pd.NaT: None}, inplace=True)

    products = products.to_dict(orient="records")
    orders = (orders
              .rename(columns={"order_date": "orderDate", "payment_date": "paymentDate", "shipping_date": "shippingDate",
                               "delivery_date": "deliveryDate", "cancel_date": "cancelDate", "return_date": "returnDate"})
              .to_dict(orient="records"))
    order_items = order_items.to_dict(orient="records")

    orders = [{
        **order,
        "items": [{
            "productId": item["product_id"],
            "quantity": item["quantity"],
            "unitPrice": item["unit_price"]
        } for item in order_items if item["order_id"] == order["id"]]
    } for order in orders]
    return products, orders

products, orders = get_data()
app = FastAPI()


@app.get("/products", response_model=List[ProductModel])
async def get_products():
    return products


@app.get("/orders", response_model=List[OrderModel])
async def get_orders():
    return orders

if __name__ == "__main__":
    uvicorn.run("api_source:app", host="127.0.0.1", port=8000, reload=True)
