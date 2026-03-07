from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from constants import ERROR_NOTIFICATION_NOT_FOUND

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Get Notifications by role
@router.get("/{role}", response_model=list[schemas.NotificationOut])
def get_notifications(role: str, db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(
        models.Notification.role == role
    ).order_by(models.Notification.created_at.desc()).all()


# Mark notification as read
@router.put("/{notification_id}")
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail=ERROR_NOTIFICATION_NOT_FOUND)

    notification.is_read = 1
    db.commit()

    return {"message": "Marked as read"}
