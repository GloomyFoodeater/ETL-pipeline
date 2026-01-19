from pydantic import BaseModel


class OrderItemModel(BaseModel):
    productId: int
    quantity: int
    unitPrice: int
