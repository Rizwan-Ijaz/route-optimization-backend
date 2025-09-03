from pydantic import BaseModel, UUID4, Field
from datetime import time

# Pydantic model for a Vehicle.
# The `BaseModel` handles automatic data validation and parsing.
class VehicleModel(BaseModel):
    """
    A Pydantic model representing a vehicle.

    This class defines the expected data types and structure for vehicle records,
    providing validation to ensure data integrity. The `Config` class allows
    for automatic conversion between snake_case (Python convention) and
    camelCase (common in JSON/JavaScript).
    """

    # The unique identifier for the vehicle. Using UUID4 for a UUID string.
    id: UUID4

    # The total number of seats.
    # The `Field` alias is used to map the JSON key to the Python variable name.
    total_seats: int = Field(..., alias="totalSeats")

    # The number of foldable seats.
    foldable_seats: int = Field(..., alias="foldableSeats")

    # The start time of the shift. The `datetime.time` type ensures
    # the string is in a valid time format (e.g., 'HH:MM').
    shift_start: time = Field(..., alias="shiftStart")

    # The end time of the shift.
    shift_end: time = Field(..., alias="shiftEnd")

    # The Config class provides settings for the model.
    class Config:
        # `populate_by_name` allows Pydantic to accept both the
        # aliased name and the field name when parsing data.
        populate_by_name = True