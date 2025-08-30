from pydantic import BaseModel
from typing import Optional

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class Booking(BaseModel):
    id: str
    customer: Optional[str] = None
    passengers: int = 0
    wheelchairs: int = 0
    pickupTime: str  # ISO format
    pickupAddress: Optional[str] = None
    deliveryTime: str  # ISO format
    deliveryAddress: Optional[str] = None
    pickup: Coordinates
    delivery: Coordinates

    class Config:
        from_attributes = True