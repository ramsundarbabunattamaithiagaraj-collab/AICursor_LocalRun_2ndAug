from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.inventory import InventoryAdjust, InventoryCreate, InventoryRead
from app.services.inventory_service import InventoryService
from app.utils.exceptions import DuplicateResourceError, InsufficientStockError, NotFoundError

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


@router.post("", response_model=InventoryRead, status_code=status.HTTP_201_CREATED)
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db)) -> InventoryRead:
    try:
        return InventoryService(db).create(payload)
    except (DuplicateResourceError, NotFoundError) as exc:
        code = status.HTTP_409_CONFLICT if isinstance(exc, DuplicateResourceError) else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("/low-stock", response_model=list[InventoryRead])
def list_low_stock(db: Session = Depends(get_db)) -> list[InventoryRead]:
    return InventoryService(db).list_low_stock()


@router.get("/product/{product_id}", response_model=list[InventoryRead])
def list_for_product(product_id: int, db: Session = Depends(get_db)) -> list[InventoryRead]:
    return InventoryService(db).list_for_product(product_id)


@router.post("/{inventory_id}/adjust", response_model=InventoryRead)
def adjust_stock(inventory_id: int, payload: InventoryAdjust, db: Session = Depends(get_db)) -> InventoryRead:
    try:
        return InventoryService(db).adjust_stock(inventory_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
