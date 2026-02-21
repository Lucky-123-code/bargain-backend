from pydantic import BaseModel

class OfferRequest(BaseModel):
    product_id: int
    offer_price: float