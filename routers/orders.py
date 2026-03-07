from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from constants import ERROR_ORDER_NOT_FOUND
from notification_utils import send_order_confirmation_sms, send_order_confirmation_email
from utils import get_current_user_id

router = APIRouter(prefix="/orders", tags=["Orders"])

# Create Order
@router.post("/", response_model=schemas.OrderOut)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):

    new_order = models.Order(
        customer_name=order.customer_name,
        product_name=order.product_name,
        total_price=order.total_price,
        payment_method=order.payment_method or "cod",
        upi_id=order.upi_id
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Get user info for notifications
    user_id = get_current_user_id()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    # Get address for phone number
    address = None
    phone_number = None
    if order.address_id is not None:
        address = db.query(models.Address).filter(models.Address.id == order.address_id).first()
        if address is not None:
            phone_number = str(address.phone)
    
    # Get user email
    user_email = None
    if user is not None:
        user_email = str(user.email)
    
    # Send SMS notification
    if phone_number:
        sms_sent = send_order_confirmation_sms(
            phone=phone_number,
            order_id=new_order.id,
            total=order.total_price
        )
        new_order.sms_sent = sms_sent
    
    # Send email notification
    if user_email:
        email_sent = send_order_confirmation_email(
            email=user_email,
            order_id=new_order.id,
            total=order.total_price,
            items=[{"name": order.product_name, "quantity": 1, "price": order.total_price}]
        )
        new_order.email_sent = email_sent
    
    db.commit()
    db.refresh(new_order)

    # Create notification for admin
    notification = models.Notification(
        message=f"New order #{new_order.id} from {order.customer_name} - ₹{order.total_price} ({order.payment_method or 'COD'})",
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
        raise HTTPException(status_code=404, detail=ERROR_ORDER_NOT_FOUND)

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
