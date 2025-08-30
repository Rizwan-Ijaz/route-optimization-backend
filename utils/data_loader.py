import json
import pandas as pd
import chardet
from datetime import datetime
from io import StringIO
import pytz
from app.models.booking import Booking, Coordinates
from typing import Optional, List

def load_json_data(file_path: str) -> list[dict]:
    with open(file_path, "r") as f:
        return json.load(f)
    
def read_csv_to_json(content: bytes, override_encoding: Optional[str] = None) -> List[Booking]:
    """
    Read a CSV file from bytes and convert it to JSON.
    Args:
        content: Raw bytes of the CSV file.
        override_encoding: Optional encoding to use instead of auto-detection.
    Returns a dict with encoding, confidence, and JSON data.
    """
    # Check if content is empty
    if not content:
        raise ValueError("File content is empty")

    # Use override encoding if provided, otherwise detect encoding
    encoding = override_encoding
    confidence = 1.0  # Assume full confidence if encoding is overridden
    if encoding is None:
        result = chardet.detect(content)
        encoding = result['encoding']
        confidence = result['confidence']

        # Validate encoding detection
        if encoding is None:
            encoding = 'latin1'  # Fallback encoding
            confidence = 0.0
            print("Encoding detection failed, falling back to latin1")
        elif confidence < 0.7:  # Lowered threshold from 0.9 to 0.7
            print(f"Low confidence ({confidence:.2%}) in detected encoding: {encoding}, falling back to latin1")
            encoding = 'latin1'
            confidence = 0.0

    # Log detected or used encoding
    print(f"Using encoding: {encoding} (confidence: {confidence:.2%})")

    # Decode content
    try:
        content_str = content.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode file with encoding ({encoding}): {str(e)}")

    # Convert CSV to JSON
    try:
        df = pd.read_csv(StringIO(content_str), delimiter=';')
        
        # Debug: Print column names and first row to verify
        print(f"CSV column names: {list(df.columns)}")
        
         # Define timezones
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        utc_tz = pytz.UTC
        
        # Map CSV rows to Booking objects
        bookings = []
        
        for _, row in df.iterrows():
            # Parse dates to ISO format
            try:
                
                pickup_time_str = row.get('Vertrektijd', '')
                delivery_time_str = row.get('Aankomsttijd', '')
                
                pickup_time = None
                if pickup_time_str and str(pickup_time_str).strip():
                    pickup_time = datetime.strptime(pickup_time_str, '%d-%m-%Y %H:%M')
                    pickup_time = amsterdam_tz.localize(pickup_time).astimezone(utc_tz).isoformat()
                
                delivery_time = None
                if delivery_time_str and str(delivery_time_str).strip():
                    delivery_time = datetime.strptime(delivery_time_str, '%d-%m-%Y %H:%M')
                    delivery_time = amsterdam_tz.localize(delivery_time).astimezone(utc_tz).isoformat()
                    
                if not pickup_time or not delivery_time:
                    raise ValueError(f"Missing or invalid pickup/delivery time in row with Rit ID {row.get('Rit ID')}")
                
            except ValueError:
                raise ValueError(f"Invalid date format for pickup or delivery time in row with Rit ID {row.get('Rit ID')}")

            # Concatenate address fields
            pickup_address = ' '.join(filter(None, [
                row.get('Vertrek Straat', ''),
                str(row.get('Vertrek Huisnummer', '')),
                row.get('Vertrek Postcode', ''),
                row.get('Vertrek Stad', '')
            ])) or None

            delivery_address = ' '.join(filter(None, [
                row.get('Aankomst Straat', ''),
                str(row.get('Aankomst Huisnummer', '')),
                row.get('Aankomst Postcode', ''),
                row.get('Aankomst Stad', '')
            ])) or None

           # Concatenate customer name, handling nan
            customer = ' '.join(filter(None, [
                str(row.get('Tussenvoegsel Hoofdklant', '')) if not pd.isna(row.get('Tussenvoegsel Hoofdklant')) else '',
                str(row.get('Achternaam Hoofdklant', '')) if not pd.isna(row.get('Achternaam Hoofdklant')) else ''
            ])) or None

            # Handle passengers
            passengers = int(row.get('Passagiers', 0)) if pd.notna(row.get('Passagiers')) and str(row.get('Passagiers')).strip() else 0

            # Create Booking object
            try:
                booking = Booking(
                    id=str(row.get('Rit ID', '')),
                    customer=customer,
                    passengers=passengers,
                    pickupTime=pickup_time,
                    pickupAddress=pickup_address,
                    deliveryTime=delivery_time,
                    deliveryAddress=delivery_address,
                    pickup=Coordinates(latitude=0.0, longitude=0.0),  # Placeholder
                    delivery=Coordinates(latitude=0.0, longitude=0.0)  # Placeholder
                )
                bookings.append(booking)
            except ValueError as e:
                raise ValueError(f"Failed to validate Booking for Rit ID {row.get('Rit ID')}: {str(e)}")

        return bookings
    except pd.errors.ParserError:
        raise ValueError("Invalid CSV format")
    except Exception as e:
        raise ValueError(f"Failed to process CSV: {str(e)}")
