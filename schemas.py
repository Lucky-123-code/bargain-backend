from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ------------------------
# USER
# ------------------------

class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True


# ------------------------
# PRODUCT
# ------------------------

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    cost: float
    image: Optional[str] = None
    stock: int


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


# ------------------------
# ORDER
# ------------------------

class OrderCreate(BaseModel):
    customer_name: str
    product_name: str
    total_price: float


class OrderOut(BaseModel):
    id: int
    customer_name: str
    product_name: str
    total_price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderUpdateStatus(BaseModel):
    status: str


# ------------------------
# NOTIFICATION
# ------------------------

class NotificationOut(BaseModel):
    id: int
    message: str
    role: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------
# BARGAIN
# ------------------------

class BargainRequest(BaseModel):
    offer: float
