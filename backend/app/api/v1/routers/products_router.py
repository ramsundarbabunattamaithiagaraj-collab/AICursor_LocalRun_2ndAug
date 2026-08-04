from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService
from app.utils.exceptions import DuplicateResourceError, NotFoundError

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    try:
        return ProductService(db).create(payload)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=list[ProductRead])
def search_products(
    response: Response,
    keyword: str | None = None,
    category_id: int | None = None,
    brand: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    """Searches products with pagination. The total number of records matching
    the filters (ignoring skip/limit) is returned via the `X-Total-Count`
    response header so clients can render page counts without changing the
    response body shape."""
    service = ProductService(db)
    total = service.count(keyword, category_id, brand, active_only)
    response.headers["X-Total-Count"] = str(total)
    return service.search(keyword, category_id, brand, active_only, skip, limit)


@router.get("/sku/{sku}", response_model=ProductRead)
def get_product_by_sku(sku: str, db: Session = Depends(get_db)) -> ProductRead:
    try:
        return ProductService(db).get_by_sku(sku)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    try:
        return ProductService(db).get(product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> ProductRead:
    try:
        return ProductService(db).update(product_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    try:
        ProductService(db).delete(product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
