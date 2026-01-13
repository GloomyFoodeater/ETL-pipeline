from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from models.OrderItemModel import OrderItemModel


class OrderModel(BaseModel):
    order_id: int
    customer_id: int
    order_status: str
    order_date: datetime
    order_payment_date: Optional[datetime]
    order_shipping_date: Optional[datetime]
    order_delivery_date: Optional[datetime]
    order_cancel_date: Optional[datetime]
    order_return_date: Optional[datetime]
    items: List[OrderItemModel]
