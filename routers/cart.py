# routers/cart.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Cart, Product
from utils import get_current_user_id
from pydantic import BaseModel
from constants import ERROR_ITEM_NOT_FOUND

# Schema for cart response with product
class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    product: Optional[Dict[str, Any]]
    negotiated_price: Optional[float] = None

    class Config:
        from_attributes = True

class CartAddRequest(BaseModel):
    product_id: int
    quantity: int = 1

router = APIRouter()

@router.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., description="Product ID"),
    quantity: int = Query(1, description="Quantity"),
    negotiated_price: Optional[float] = Query(None, description="Negotiated price if bargained"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.user_id == user_id, Cart.product_id == product_id).first()
    if item:
        item.quantity = item.quantity + quantity
    else:
        item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(item)
    db.commit()
    db.refresh(item)

    # Fetch the product details
    product = db.query(Product).filter(Product.id == item.product_id).first()

    product_data: Optional[Dict[str, Any]] = None
    if product:
        product_data = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cost": product.cost,
            "image": product.image,
            "image_url": product.image_url,
            "stock": product.stock,
            "category": getattr(product, 'category', None)
        }
    return {
        "id": item.id,
        "user_id": item.user_id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "product": product_data,
        "negotiated_price": negotiated_price
    }

@router.get("/cart")
def get_cart(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    cart_items = db.query(Cart).options(joinedload(Cart.product)).filter(Cart.user_id == user_id).all()
    
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
            "product": product_data,
            "negotiated_price": getattr(item, 'negotiated_price', None)
        })
    
    return result

@router.put("/cart/{id}")
def update_cart(id: int, quantity: int = Query(1, description="Quantity"), db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=ERROR_ITEM_NOT_FOUND)
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item

@router.delete("/cart/{id}")
def delete_cart(id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = db.query(Cart).filter(Cart.id == id, Cart.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=ERROR_ITEM_NOT_FOUND)
    db.delete(item)
    db.commit()
    return {"detail": "Deleted"}

@router.delete("/cart/clear")
def clear_cart(db: Session = Depends(get_db)):
    """Clear all items from user's cart"""
    user_id = get_current_user_id()
    db.query(Cart).filter(Cart.user_id == user_id).delete()
    db.commit()
    return {"detail": "Cart cleared"}

