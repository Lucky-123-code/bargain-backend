from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ------------------------
# ADDRESS
# ------------------------

class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    pincode: str

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    pass

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
    cost: float
    image: Optional[str] = None
    image_url: Optional[str] = None
    stock: int = 0
    category: Optional[str] = None


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


# ------------------------
# LLM BARGAIN (Conversational)
# ------------------------

class BargainMessage(BaseModel):
    """A single message in the bargain conversation"""
    role: str  # "user" or "assistant" (store)
    content: str


class BargainChatRequest(BaseModel):
    """Request for LLM-powered conversational bargaining"""
    message: str
    conversation_history: list[BargainMessage] = []


class BargainChatResponse(BaseModel):
    """Response from LLM-powered conversational bargaining"""
    response: str  # The LLM's response message
    suggested_price: Optional[float] = None  # If user made an offer, the suggested counter
    is_accepted: bool = False  # If the deal was accepted
    final_price: Optional[float] = None  # Final price if accepted
    reasoning: Optional[str] = None  # LLM's reasoning for the response
