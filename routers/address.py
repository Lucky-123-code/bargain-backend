# routers/addresses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Address
from schemas import AddressCreate, AddressUpdate
from utils import get_current_user_id
from constants import ERROR_ADDRESS_NOT_FOUND

router = APIRouter()

@router.post("/addresses")
def create_address(address: AddressCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    new_address = Address(user_id=user_id, **address.model_dump())
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.get("/addresses")
def get_addresses(db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    return db.query(Address).filter(Address.user_id == user_id).all()

@router.put("/addresses/{id}")
def update_address(id: int, address: AddressUpdate, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    db_address = db.query(Address).filter(Address.id == id, Address.user_id == user_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail=ERROR_ADDRESS_NOT_FOUND)
    for key, value in address.model_dump(exclude_unset=True).items():
        setattr(db_address, key, value)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.delete("/addresses/{id}")
def delete_address(id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    db_address = db.query(Address).filter(Address.id == id, Address.user_id == user_id).first()
    if not db_address:
        raise HTTPException(status_code=404, detail=ERROR_ADDRESS_NOT_FOUND)
    db.delete(db_address)
    db.commit()
    return {"detail": "Deleted"}