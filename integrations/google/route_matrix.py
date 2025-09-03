import googlemaps
from core.config import settings
import json
import os

gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)

CACHE_FILE = "distance_matrix_cache.json"

def build_matrices(response):
    """Builds distance and time sub-matrices from Distance Matrix API response.
       Ensures consistent [num_origins x num_destinations] shape."""
    distance_matrix = []
    time_matrix = []

    for row in response.get("rows", []):
        dist_row, time_row = [], []
        for element in row.get("elements", []):
            if element.get("status") == "OK":
                # Distance in meters
                dist_row.append(element["distance"]["value"])
                # Duration in seconds
                time_row.append(element["duration"]["value"])
            else:
                # If no route, assign large penalties
                dist_row.append(10**9)
                time_row.append(10**9)
        distance_matrix.append(dist_row)
        time_matrix.append(time_row)

    return distance_matrix, time_matrix


def create_matrices(addresses, force_refresh=False):
    """Builds both distance and time matrices for given addresses."""
    # if not force_refresh and os.path.exists(CACHE_FILE):
    #     with open(CACHE_FILE, "r") as f:
    #         cache = json.load(f)
    #         return cache["distance_matrix"], cache["time_matrix"]

    num_addresses = len(addresses)
    distance_matrix = [[0] * num_addresses for _ in range(num_addresses)]
    time_matrix = [[0] * num_addresses for _ in range(num_addresses)]

    max_elements = 100
    max_origins = 25
    max_destinations = 25
    max_rows = min(max_elements // max_destinations, max_origins)
    max_cols = min(max_elements // max_rows, max_destinations)

    for i in range(0, num_addresses, max_rows):
        origin_addresses = addresses[i:i + max_rows]

        for j in range(0, num_addresses, max_cols):
            dest_addresses = addresses[j:j + max_cols]

            response = send_request(origin_addresses, dest_addresses)

            print(" =======================\n")
            print(json.dumps(response, indent=2))
            print(" =======================\n")

            sub_distance, sub_time = build_matrices(response)

            # Stitch the sub-matrices into correct global indices
            for oi, (dist_row, time_row) in enumerate(zip(sub_distance, sub_time)):
                for dj, (dist_val, time_val) in enumerate(zip(dist_row, time_row)):
                    distance_matrix[i + oi][j + dj] = dist_val
                    time_matrix[i + oi][j + dj] = time_val

    # ✅ Cache result
    # with open(CACHE_FILE, "w") as f:
    #     json.dump({
    #         "addresses": addresses,
    #         "distance_matrix": distance_matrix,
    #         "time_matrix": time_matrix
    #     }, f, indent=2)

    return distance_matrix, time_matrix

def send_request(origin_addresses, dest_addresses):
  """ Build and send request for the given origin and destination addresses."""
  
  response = gmaps.distance_matrix(origin_addresses,dest_addresses, 'driving', 'imperial')
  return response