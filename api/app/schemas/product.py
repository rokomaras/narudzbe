# =============================================================
# product.py — sheme za proizvode
# =============================================================
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    price_cents: int = Field(gt=0, le=100_000_000)
    stock: int = Field(ge=0, le=1_000_000)
    is_active: bool = True


class ProductUpdate(BaseModel):
    """PATCH: sva polja su opcionalna, mijenja se samo ono što je poslano."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    price_cents: Optional[int] = Field(default=None, gt=0, le=100_000_000)
    stock: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price_cents: int
    stock: int
    is_active: bool

    model_config = {"from_attributes": True}
