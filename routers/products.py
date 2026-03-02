from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter()

@router.get("/products")
def get_products(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = db.execute(text("SELECT * FROM products ORDER BY id DESC")).mappings().all()
    return [dict(row) for row in rows]


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    row = db.execute(
        text("SELECT * FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    return dict(row)
