from pydantic import BaseModel


class OrderItemModel(BaseModel):
    product_id: int
    order_item_quantity: int
    order_item_unit_price: int
