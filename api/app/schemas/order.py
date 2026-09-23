# =============================================================
# order.py — sheme za narudžbe
# =============================================================
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100)


class OrderItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=5, max_length=255)
    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def _no_duplicate_products(self):
        ids = [i.product_id for i in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Isti proizvod ne smije biti dvaput u narudžbi")
        return self


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    customer_username: str
    status: str
    shipping_address: str
    total_cents: int
    created_at: datetime
    paid_at: Optional[datetime]
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}
