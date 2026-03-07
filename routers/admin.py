from typing import Any, Dict, List
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from schemas import ProductCreate, OrderUpdateStatus
from database import get_db
from constants import ERROR_PRODUCT_NOT_FOUND, ERROR_ORDER_NOT_FOUND

router = APIRouter(prefix="/admin")

@router.post("/add-product")
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    db.execute(
        text(
            """
            INSERT INTO products (name, description, price, cost, image, image_url, stock, category)
            VALUES (:name, :description, :price, :cost, :image, :image_url, :stock, :category)
            """
        ),
        {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cost": product.cost,
            "image": product.image,
            "image_url": product.image_url,
            "stock": product.stock,
            "category": product.category,
        },
    )
    db.commit()

    return {"message": "Product added"}


@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    result = db.execute(
        text(
            """
            UPDATE products 
            SET name = :name, description = :description, price = :price, 
                cost = :cost, image = :image, image_url = :image_url,
                stock = :stock, category = :category
            WHERE id = :product_id
            """
        ),
        {
            "product_id": product_id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "cost": product.cost,
            "image": product.image,
            "image_url": product.image_url,
            "stock": product.stock,
            "category": product.category,
        },
    )
    db.commit()
    
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail=ERROR_PRODUCT_NOT_FOUND)
    
    return {"message": "Product updated"}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    result = db.execute(
        text("DELETE FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    )
    db.commit()
    
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail=ERROR_PRODUCT_NOT_FOUND)
    
    return {"message": "Product deleted"}


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


@router.put("/orders/{order_id}")
def update_order_status(order_id: int, status_update: OrderUpdateStatus, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Update order status - expects {status: 'new_status'} in body"""
    result = db.execute(
        text("UPDATE orders SET status = :status WHERE id = :order_id"),
        {"status": status_update.status, "order_id": order_id},
    )
    db.commit()
    
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail=ERROR_ORDER_NOT_FOUND)
    
    return {"message": "Order status updated"}


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


@router.get("/dashboard-stats")
def dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get detailed dashboard statistics"""
    # Total products
    total_products = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
    
    # Total orders
    total_orders = db.execute(text("SELECT COUNT(*) FROM orders")).scalar() or 0
    
    # Total revenue
    revenue = db.execute(text("SELECT COALESCE(SUM(total_price), 0) FROM orders")).scalar() or 0
    
    # Pending orders
    pending_orders = db.execute(
        text("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    ).scalar() or 0
    
    # Low stock products (stock < 10)
    low_stock = db.execute(
        text("SELECT COUNT(*) FROM products WHERE stock < 10")
    ).scalar() or 0
    
    # Recent orders (last 5)
    recent_orders = db.execute(
        text("SELECT id, customer_name, product_name, total_price, status, created_at FROM orders ORDER BY id DESC LIMIT 5")
    ).mappings().all()
    
    return {
        "total_products": int(total_products),
        "total_orders": int(total_orders),
        "revenue": float(revenue),
        "pending_orders": int(pending_orders),
        "low_stock": int(low_stock),
        "recent_orders": [dict(row) for row in recent_orders]
    }


@router.get("/users")
def get_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all users"""
    rows = db.execute(
        text("SELECT id, name, email, created_at FROM users ORDER BY id DESC")
    ).mappings().all()
    return [dict(row) for row in rows]


# Admin login (simplified - in production use proper JWT/auth)
@router.post("/login")
def admin_login(credentials: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Admin login - expects {username, password}"""
    username: Optional[str] = credentials.get("username")
    password: Optional[str] = credentials.get("password")
    
    # For demo purposes - in production use proper password hashing
    admin = db.execute(
        text("SELECT id, username FROM admin WHERE username = :username AND password = :password"),
        {"username": username, "password": password}
    ).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "message": "Login successful",
        "admin_id": admin[0],
        "username": admin[1]
    }


@router.post("/logout")
def admin_logout() -> Dict[str, str]:
    """Admin logout"""
    return {"message": "Logout successful"}
