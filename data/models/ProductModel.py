from pydantic import BaseModel


class ProductModel(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    price: int
