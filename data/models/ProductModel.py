from pydantic import BaseModel


class ProductModel(BaseModel):
    product_id: int
    product_sku: str
    product_name: str
    product_category: str
    product_price: int
