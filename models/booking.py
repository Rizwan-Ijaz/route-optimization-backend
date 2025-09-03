from pydantic import BaseModel, Field
from datetime import datetime

# Pydantic model for the Coordinates.
# This model represents a location with latitude and longitude.
class Coordinates(BaseModel):
    """
    Pydantic model for geographical coordinates.
    """
    latitude: float
    longitude: float


# Pydantic model for a Booking.
# This model represents a single booking with all its details.
class Booking(BaseModel):
    """
    Pydantic model for a booking record.
    """

    id: str

    # The customer's name.
    customer: str

    # The number of passengers.
    passengers: int

    # The pickup time, parsed as a Python datetime object.
    pickup_time: datetime = Field(..., alias="pickupTime")

    # The full pickup address string.
    pickup_address: str = Field(..., alias="pickupAddress")

    # The delivery time, parsed as a Python datetime object.
    delivery_time: datetime = Field(..., alias="deliveryTime")

    # The full delivery address string.
    delivery_address: str = Field(..., alias="deliveryAddress")

    # A nested Pydantic model for the pickup coordinates.
    pickup: Coordinates

    # A nested Pydantic model for the delivery coordinates.
    delivery: Coordinates

    class Config:
        # Allows fields to be populated by their alias (e.g., 'pickupTime').
        populate_by_name = True