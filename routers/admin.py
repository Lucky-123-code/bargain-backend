from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import ProductCreate

router = APIRouter(prefix="/admin")

@router.post("/add-product")
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
            INSERT INTO products (name, description, price, cost, image, stock)
            VALUES (:name, :description, :price, :cost, :image, :stock)
            """
        ),
        {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cost": product.cost,
            "image": product.image,
            "stock": product.stock,
        },
    )
    db.commit()

    return {"message": "Product added"}


@router.get("/orders")
def get_orders(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, customer_name, product_name, total_price, status, created_at
            FROM orders
            ORDER BY id DESC
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    products = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
    orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar() or 0
    revenue = db.execute(text("SELECT COALESCE(SUM(total_price), 0) FROM orders")).scalar() or 0

    return {
        "total_products": int(products),
        "total_orders": int(orders),
        "revenue": float(revenue),
    }
