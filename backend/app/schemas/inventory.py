from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    product_id: int
    location_code: str = Field(..., min_length=1, max_length=50)
    quantity_available: int = Field(..., ge=0)
    reorder_level: int = Field(default=10, ge=0)


class InventoryCreate(InventoryBase):
    pass


class InventoryAdjust(BaseModel):
    delta: int = Field(..., description="Positive to add stock, negative to remove stock.")
    reason: str = Field(..., min_length=1, max_length=200)


class InventoryRead(InventoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    needs_reorder: bool
    updated_at: datetime
