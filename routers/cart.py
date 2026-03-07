# routers/cart.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Cart
from utils import get_current_user_id
from pydantic import BaseModel

# Schema for cart response with product
class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    product: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

router = APIRouter()

@router.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.user_id == user_id, Cart.product_id == product_id).first()
    if item:
        item.quantity += quantity
    else:
        item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/cart")
def get_cart(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    cart_items = db.query(Cart).options(joinedload(Cart.product)).filter(Cart.user_id == user_id).all()
    
    # Format response to include product data
    result: List[Dict[str, Any]] = []
    for item in cart_items:
        product_data: Optional[Dict[str, Any]] = None
        if item.product:
            product_data = {
                "id": item.product.id,
                "name": item.product.name,
                "description": item.product.description,
                "price": item.product.price,
                "cost": item.product.cost,
                "image": item.product.image,
                "image_url": item.product.image_url,
                "stock": item.product.stock,
                "category": getattr(item.product, 'category', None)
            }
        result.append({
            "id": item.id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product": product_data
        })
    
    return result

@router.put("/cart/{id}")
def update_cart(id: int, quantity: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item

@router.delete("/cart/{id}")
def delete_cart(id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"detail": "Deleted"}
