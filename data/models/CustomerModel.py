from datetime import datetime

from pydantic import BaseModel, EmailStr


class CustomerModel(BaseModel):
    customer_id: int
    customer_email: EmailStr
    customer_last_name: str
    customer_first_name: str
    customer_registration_date: datetime
