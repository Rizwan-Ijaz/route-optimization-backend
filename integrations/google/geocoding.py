import googlemaps
from core.config import settings
import asyncio
from typing import Tuple

gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)

async def geocode_address_async(address: str) -> Tuple[float, float]:
    """Async wrapper for geocoding using ThreadPoolExecutor"""
    loop = asyncio.get_event_loop()
    
    def _geocode():
        result = gmaps.geocode(address)
        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
        raise ValueError(f"Geocoding failed for address: {address}")
    
    # Run the blocking geocoding call in a thread pool
    return await loop.run_in_executor(None, _geocode)