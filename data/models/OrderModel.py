from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from .OrderItemModel import OrderItemModel


class OrderModel(BaseModel):
    id: int
    status: str
    orderDate: datetime
    paymentDate: Optional[datetime]
    shippingDate: Optional[datetime]
    deliveryDate: Optional[datetime]
    cancelDate: Optional[datetime]
    returnDate: Optional[datetime]
    items: List[OrderItemModel]
