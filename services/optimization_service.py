import asyncio
from models.booking import Booking, Coordinates
from integrations.google.route_matrix import create_matrices
from integrations.google.geocoding import geocode_address_async
from typing import Tuple, List
from fastapi import HTTPException

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from utils.common import datetime_to_seconds, seconds_to_hhmm, to_dict

def create_data_model(bookings, locations):
    """Stores the data for the routing problem."""
    # Build distance & time matrices from Google API response
    distance_matrix, time_matrix = create_matrices(locations)
    
    data = {}
    data["bookings"] = bookings
    data["distance_matrix"] = distance_matrix
    data["time_matrix"] = time_matrix
    data["depot"] = 0

    pickups_deliveries = []
    time_windows = []
    seat_demands = [0]  # depot demand is 0
    wheelchair_demands = [0]  # depot demand is 0
    booking_map = {}

    # Depot placeholder, will update later
    time_windows.append((0, 0))  

    earliest_pickup = float("inf")
    latest_delivery = 0

    for i, booking in enumerate(bookings, start=1):
        booking_id = booking.id

        # convert datetime → seconds
        pickup_time = datetime_to_seconds(booking.pickupTime)
        delivery_time = datetime_to_seconds(booking.deliveryTime)

        # pickup window ±25 mins
        pickup_start = pickup_time - 1500
        pickup_end = pickup_time + 1500

        # delivery window up to +25 mins
        delivery_start = delivery_time
        delivery_end = delivery_time + 1500

        # store booking mapping with demands
        seat_demand = booking.passengers
        wheelchair_demand = booking.wheelchairs  # Remove getattr to assume attribute always present; raises error if missing

        seat_demands.append(seat_demand)
        seat_demands.append(-seat_demand)
        wheelchair_demands.append(wheelchair_demand)
        wheelchair_demands.append(-wheelchair_demand)
        

        booking_map[i * 2 - 1] = {
            "id": booking_id,
            "type": "pickup",
            "address": booking.pickupAddress,
            "window": (pickup_start, pickup_end),
            "seats_demand": seat_demand,
            "wheelchair_demand": wheelchair_demand,
        }
        booking_map[i * 2] = {
            "id": booking_id,
            "type": "delivery",
            "address": booking.deliveryAddress,
            "window": (delivery_start, delivery_end),
            "seats_demand": -seat_demand,
            "wheelchair_demand": -wheelchair_demand,
        }

        # add pickup + delivery
        pickups_deliveries.append((i * 2 - 1, i * 2))
        time_windows.append((pickup_start, pickup_end))
        time_windows.append((delivery_start, delivery_end))

        # track global min/max
        earliest_pickup = min(earliest_pickup, pickup_start)
        latest_delivery = max(latest_delivery, delivery_end)

    # Dynamic depot window: earliest pickup − 1h, latest delivery + 1h
    depot_start = max(0, earliest_pickup - 3600)
    depot_end = latest_delivery + 3600
    time_windows[0] = (depot_start, depot_end)
    
    
    data["pickups_deliveries"] = pickups_deliveries
    data["time_windows"] = time_windows
    data["booking_map"] = booking_map
    data["num_vehicles"] = 4
    data["seat_capacities"] = [8, 8, 8, 8]  # All vehicles have 8 total seats
    data["wheelchair_capacities"] = [2, 2, 2, 0] # Vehicle 3 has no wheelchair space
    data["seat_demands"] = seat_demands
    data["wheelchair_demands"] = wheelchair_demands
    return data

def print_solution(data, manager, routing, solution, time_dimension):
    """Prints solution on console with detailed debug logs for seats and wheelchairs."""
    
    # Get the capacity dimensions
    seats_dimension = routing.GetDimensionOrDie("Seats")
    wheelchair_dimension = routing.GetDimensionOrDie("WheelchairSpaces")
    
    total_distance = 0
    total_time = 0
    
    # Iterate through each vehicle to print its route
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_info = f"Route for vehicle {vehicle_id}:\n"
        
        while not routing.IsEnd(index):
            # Get node and vehicle information
            node_index = manager.IndexToNode(index)
            
            # Get cumulative values for distance, time, seats, and wheelchairs
            distance_var = routing.GetDimensionOrDie("Distance").CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            seats_var = seats_dimension.CumulVar(index)
            wheelchair_var = wheelchair_dimension.CumulVar(index)
            
            # Print detailed debug logs for the current node
            route_info += (
                f"  Node {node_index} "
                f"(Distance: {solution.Value(distance_var)}m, "
                f"Time: {solution.Value(time_var)}s, "
                f"Seats: {solution.Value(seats_var)}, "
                f"Wheelchairs: {solution.Value(wheelchair_var)}) ->\n"
            )
            
            # Move to the next node in the route
            next_index = solution.Value(routing.NextVar(index))
            index = next_index
            
        # Add the end node and final stats
        node_index = manager.IndexToNode(index)
        final_distance = solution.Value(routing.GetDimensionOrDie("Distance").CumulVar(index))
        final_time = solution.Value(time_dimension.CumulVar(index))
        
        route_info += (
            f"  Node {node_index} "
            f"(Distance: {final_distance}m, "
            f"Time: {final_time}s)\n"
        )
        route_info += f"  Total Route Distance: {final_distance}m\n"
        route_info += f"  Total Route Time: {final_time}s\n"
        
        total_distance += final_distance
        total_time += final_time
        
        # Print the complete route for the vehicle
        print(route_info)

    # Print overall solution summary
    print(f"Total Distance of all routes: {total_distance}m")
    print(f"Total Time of all routes: {total_time}s")

def optimize_routes(bookings_data: List[Booking]) -> None:
    """Optimize pickup and delivery routes with distance + time windows."""

    # Prepare locations (lat,lng) and index map
    locations, index_map = prepare_locations(bookings_data)

    # Build problem data
    data = create_data_model(bookings_data, locations)

    # Routing index manager
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    routing = pywrapcp.RoutingModel(manager)

    # ----------- Distance Dimension ----------- #
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    dist_cb_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(dist_cb_index)

    routing.AddDimension(
        dist_cb_index,
        0,
        2_000_000,
        True,
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # ----------- Time Dimension ----------- #
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        service_time = 300 if to_node != data["depot"] else 0  # 5 min service at non-depot nodes
        return data["time_matrix"][from_node][to_node] + service_time

    time_cb_index = routing.RegisterTransitCallback(time_callback)

    max_horizon = max(tw[1] for tw in data["time_windows"]) + 86400  # Add buffer

    routing.AddDimension(
        time_cb_index,
        43200,  # 12 hours slack for bridging time gaps
        max_horizon,
        False,
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(50)  # Penalize long route spans

    # Apply time windows
    for loc_idx, tw in enumerate(data["time_windows"]):
        start, end = tw
        if loc_idx == data["depot"]:
            # depot window is set to cover earliest pickup - 1h to latest delivery + 1h
            index = manager.NodeToIndex(loc_idx)
            time_dimension.CumulVar(index).SetRange(start, end)
        else:
            index = manager.NodeToIndex(loc_idx)
            time_dimension.CumulVar(index).SetRange(start, end)
    

    depot_idx = data["depot"]
    for vehicle_id in range(data["num_vehicles"]):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)

        start, end = data["time_windows"][depot_idx]

        time_dimension.CumulVar(start_index).SetRange(start, end)
        time_dimension.CumulVar(end_index).SetRange(start, end)

        # Minimize start & end times
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start_index))
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_index))


    # ----------- Seat & Wheelchair Capacity Dimensions ----------- #
    
    def seat_demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["seat_demands"][from_node]

    seat_demand_callback_index = routing.RegisterUnaryTransitCallback(seat_demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        seat_demand_callback_index,
        0,  # null capacity slack
        data["seat_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        "Seats",
    )
    
    seats_dimension = routing.GetDimensionOrDie("Seats")
    
    def wheelchair_demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["wheelchair_demands"][from_node]

    wheelchair_demand_callback_index = routing.RegisterUnaryTransitCallback(wheelchair_demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        wheelchair_demand_callback_index,
        0,  # null capacity slack
        data["wheelchair_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        "WheelchairSpaces",
    )
    wheelchair_dimension = routing.GetDimensionOrDie("WheelchairSpaces")
   
   
   # Add the constraint for each vehicle
    for vehicle_id in range(data["num_vehicles"]):
        # The total number of effective seats must not exceed 8 at any point
        # on the vehicle's route.
        routing.solver().Add(
            seats_dimension.CumulVar(routing.End(vehicle_id)) +
            2 * wheelchair_dimension.CumulVar(routing.End(vehicle_id)) <= 8
        )

        # To be more precise, this must hold at every node
        for node_index in range(manager.GetNumberOfNodes()):
            if node_index != manager.GetNumberOfNodes() - 1: # exclude the last dummy node
                routing.solver().Add(
                    seats_dimension.CumulVar(node_index) +
                    2 * wheelchair_dimension.CumulVar(node_index) <= 8
                )

    # ----------- Pickup & Delivery Constraints ----------- #
    for pickup, delivery in data["pickups_deliveries"]:
        pickup_idx = manager.NodeToIndex(pickup)
        delivery_idx = manager.NodeToIndex(delivery)

        routing.AddPickupAndDelivery(pickup_idx, delivery_idx)
        routing.solver().Add(
            routing.VehicleVar(pickup_idx) ==
            routing.VehicleVar(delivery_idx)
        )
        routing.solver().Add(
            time_dimension.CumulVar(pickup_idx) <=
            time_dimension.CumulVar(delivery_idx)
        )
        
        # Prefer early drop-offs
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(delivery_idx))


        # Debugging: print each pair
        print(
            f"Pickup {pickup} -> Delivery {delivery}, "
            f"Pickup TW {data['time_windows'][pickup]}, "
            f"Delivery TW {data['time_windows'][delivery]}"
        )
   
    # ----------- Booking Disjunctions (allow skipping) ----------- #
    penalty = 100000000  # Higher penalty to strongly prefer serving all
    zero_penalty = 0

    for pickup, delivery in data["pickups_deliveries"]:
        pickup_idx = manager.NodeToIndex(pickup)
        delivery_idx = manager.NodeToIndex(delivery)

        solver = routing.solver()
        # Ensure pickup not visited without delivery
        solver.Add(routing.ActiveVar(delivery_idx) >= routing.ActiveVar(pickup_idx))

        # Disjunctions: Penalty on delivery (for not serving), free on pickup
        routing.AddDisjunction([delivery_idx], penalty)
        routing.AddDisjunction([pickup_idx], zero_penalty)
        


    # ----------- Search Parameters ----------- #
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    search_params.time_limit.seconds = 30
    # search_params.log_search = True
    
    # Debugging: print problem overview
    print("=== Routing Problem Overview ===")
    print("Num Vehicles:", data["num_vehicles"])
    print("Depot:", data["depot"])
    print("Pickups & Deliveries:", data["pickups_deliveries"])
    print("Time Windows:", data["time_windows"])
    print("Seat Demands:", data["seat_demands"])
    print("Wheelchairs Demands:", data["wheelchair_demands"])
  
    print("==============================")

    # ----------- Solve ----------- #
    solution = routing.SolveWithParameters(search_params)

    if solution:
        print_solution(data, manager, routing, solution,time_dimension)
        formatted_solution = extract_solution(data, manager, routing, solution, time_dimension)
        return formatted_solution
    else:
        print("❌ No solution found!")

    return "No solution found!"

def extract_solution(data, manager, routing, solution, time_dimension):
    """Return structured clusters with full booking objects, path info, and dropped bookings."""

    # Map node indices to booking and type information
    node_mapping = {}
    for idx, (pickup, delivery) in enumerate(data['pickups_deliveries']):
        booking = data["bookings"][idx]  # full booking object
        node_mapping[manager.NodeToIndex(pickup)] = (idx, "Pickup", booking)
        node_mapping[manager.NodeToIndex(delivery)] = (idx, "Dropoff", booking)

    clusters = []
    dropped_bookings = set()
    assigned_booking_indices = set()

    # Process each vehicle route
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_path = []
        bookings_in_route = {}

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            arrival_time = solution.Value(time_dimension.CumulVar(index))
            
            # Get the node's details from the mapping
            details = node_mapping.get(node_index)

            # Build the path and collect booking info
            stop_info = {
                "node_index": node_index,
                "arrival_time": arrival_time,
            }
            if details:
                idx, label, booking = details
                assigned_booking_indices.add(idx)
                stop_info.update({
                    "type": label,
                    "booking_id": booking.id
                })

                # Store booking-specific times for the cluster output
                if idx not in bookings_in_route:
                    bookings_in_route[idx] = {
                        "booking": booking.copy() if isinstance(booking, dict) else booking.model_dump(),
                    }
                if label == "Pickup":
                    bookings_in_route[idx]["pickup_time"] = arrival_time
                else:
                    bookings_in_route[idx]["dropoff_time"] = arrival_time
          
            route_path.append(stop_info)
            index = solution.Value(routing.NextVar(index))

        # Add the final stop (depot)
        final_time = solution.Value(time_dimension.CumulVar(index))
        route_path.append({
            "node_index": manager.IndexToNode(index),
            "arrival_time": final_time,
        })

        if bookings_in_route:
            clusters.append({
                "vehicle_id": vehicle_id,
                "bookings": list(bookings_in_route.values()),
                "path": route_path
            })

    # Detect dropped nodes
    all_booking_indices = set(range(len(data['bookings'])))
    dropped_booking_indices = all_booking_indices - assigned_booking_indices

    return {
        "clusters": to_dict(clusters),
        "dropped_bookings": [data["bookings"][i] for i in sorted(list(dropped_booking_indices))]
    }

def prepare_locations(bookings_data):
    """Extract all pickup & delivery locations and create an index map, with a dummy depot at index 0."""
    locations = []
    index_map = {}

    # Step 1: Add dummy depot at index 0
    dummy_depot = (51.92173421692392, 4.487105575001821)   # or you can put your office coords
    locations.append(dummy_depot)
    index_map["depot"] = 0

    # Step 2: Add pickups & deliveries after depot
    for idx, booking in enumerate(bookings_data):
        if booking.pickup:
            pickup_coord = (booking.pickup.latitude, booking.pickup.longitude)
            index_map[f"{booking.id}_pickup"] = len(locations)
            locations.append(pickup_coord)

        if booking.delivery:
            delivery_coord = (booking.delivery.latitude, booking.delivery.longitude)
            index_map[f"{booking.id}_delivery"] = len(locations)
            locations.append(delivery_coord)

    return locations, index_map


async def process_booking_geocoding(booking, semaphore: asyncio.Semaphore) -> None:
    """Process geocoding for a single booking with rate limiting"""
    async with semaphore:  # Limit concurrent requests
        tasks = []
        
        # Check if pickup geocoding is needed
        if (booking.pickupAddress and 
            (not booking.pickup or (booking.pickup.latitude == 0.0 and booking.pickup.longitude == 0.0))):
            tasks.append(('pickup', geocode_address_async(booking.pickupAddress)))
        
        # Check if delivery geocoding is needed
        if (booking.deliveryAddress and 
            (not booking.delivery or (booking.delivery.latitude == 0.0 and booking.delivery.longitude == 0.0))):
            tasks.append(('delivery', geocode_address_async(booking.deliveryAddress)))
        
        # Execute geocoding tasks concurrently for this booking
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            for i, (location_type, result) in enumerate(zip([task[0] for task in tasks], results)):
                if isinstance(result, Exception):
                    raise HTTPException(status_code=400, detail=str(result))
                
                lat, lng = result
                if location_type == 'pickup':
                    booking.pickup = Coordinates(latitude=lat, longitude=lng)
                else:  # delivery
                    booking.delivery = Coordinates(latitude=lat, longitude=lng)