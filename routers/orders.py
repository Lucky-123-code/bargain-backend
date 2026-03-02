from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/orders", tags=["Orders"])

# Create Order
@router.post("/", response_model=schemas.OrderOut)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):

    new_order = models.Order(
        customer_name=order.customer_name,
        product_name=order.product_name,
        total_price=order.total_price
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Create notification for admin
    notification = models.Notification(
        message=f"New order from {order.customer_name}",
        role="admin"
    )

    db.add(notification)
    db.commit()

    return new_order


# Get All Orders (Admin)
@router.get("/", response_model=list[schemas.OrderOut])
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).all()


# Update Order Status (Admin)
@router.put("/{order_id}")
def update_order_status(order_id: int, status_update: schemas.OrderUpdateStatus, db: Session = Depends(get_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status_update.status
    db.commit()

    # Notify customer
    notification = models.Notification(
        message=f"Your order #{order.id} is now {order.status}",
        role="customer"
    )

    db.add(notification)
    db.commit()

    return {"message": "Order status updated"}
