from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import BargainRequest

router = APIRouter()

@router.post("/bargain/{product_id}")
def bargain(product_id: int, data: BargainRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    product = db.execute(
        text("SELECT price, cost, stock FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    price, cost, stock = product

    if stock <= 0:
        return {"status": "rejected", "message": "Out of stock"}

    minimum_price = round(cost * 1.5, 2)

    if data.offer >= price:
        final_price = price
    elif data.offer >= minimum_price:
        final_price = data.offer
    else:
        return {
            "status": "counter",
            "counter_price": minimum_price
        }

    db.execute(
        text("UPDATE products SET stock = stock - 1 WHERE id = :product_id"),
        {"product_id": product_id},
    )
    db.commit()

    return {
        "status": "accepted",
        "final_price": final_price
    }
