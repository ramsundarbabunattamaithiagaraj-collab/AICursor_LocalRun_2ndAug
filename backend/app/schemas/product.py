from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    brand: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int
    variant: str | None = None
    size: str | None = None
    color: str | None = None
    list_price: float = Field(..., gt=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    tax_percent: float = Field(default=0.0, ge=0, le=100)
    is_active: bool = True

    @field_validator("sku")
    @classmethod
    def sku_must_be_uppercase_alnum(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("SKU must not be empty.")
        return cleaned


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    brand: str | None = None
    description: str | None = None
    category_id: int | None = None
    variant: str | None = None
    size: str | None = None
    color: str | None = None
    list_price: float | None = Field(default=None, gt=0)
    discount_percent: float | None = Field(default=None, ge=0, le=100)
    tax_percent: float | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    selling_price: float
    created_at: datetime
