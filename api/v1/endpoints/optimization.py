from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from core.config import settings
from models.booking import Booking
from services.optimization_service import optimize_routes
from pydantic import BaseModel, HttpUrl
import uuid
import time
import requests

# from app.utils.data_loader import read_csv_to_json
# from typing import List
import asyncio
from services.optimization_service import process_booking_geocoding
# from app.services.tsp_optimization_service import main
import json

router = APIRouter()

class LongRunningJobRequest(BaseModel):
    data: list[Booking]
    webhook_url: HttpUrl

@router.post("/start-job-with-webhook")
async def start_job_with_webhook(request: LongRunningJobRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    background_tasks.add_task(process_and_notify, job_id, request.data, str(request.webhook_url))
    return {"job_id": job_id, "message": "Job started. A webhook will be sent upon completion."}

async def process_and_notify(job_id: str, data: list[Booking], webhook_url: str):
    print(f"Starting job {job_id} with bookings_data and webhook_url: {webhook_url}")
    
    # Create semaphore to limit concurrent geocoding requests (adjust based on API limits)
    # Google Maps API allows up to 50 QPS by default, so we use 10 concurrent requests
    # semaphore = asyncio.Semaphore(10)
    
  
    # Process all bookings concurrently
    # tasks = [process_booking_geocoding(booking, semaphore) for booking in bookings_data]  
    # await asyncio.gather(*tasks)
    
    bookings_data = []
  
    for booking in updated_bookings:
        # Validate each booking using Pydantic
        try:
            bookings_data.append(Booking(**booking))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid booking data: {str(e)}")
    
    optimized_routes = optimize_routes(bookings_data)
    
    result = {"job_id": job_id, "status": "completed", "optimized_routes": optimized_routes}
    
    try:
        response = requests.post(webhook_url, json=result)
        response.raise_for_status()
        print(f"Successfully sent webhook for job {job_id}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook for job {job_id}: {e}")

@router.get('/')
async def get_optimized_routes():
    
    clusters = []
    with open('optimized_routes_response.json', 'r') as f:
        data = json.load(f)
        clusters = data['clusters']
        
    return clusters

@router.post("/")
async def run_optimization():
   
    # Validate that the uploaded file is a CSV
    # if not bookings_file.filename.endswith(".csv"):
    #     raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # content = await bookings_file.read()
    # bookings_data_1 = read_csv_to_json(content)
    
    # Create semaphore to limit concurrent geocoding requests (adjust based on API limits)
    # Google Maps API allows up to 50 QPS by default, so we use 10 concurrent requests
    # semaphore = asyncio.Semaphore(10)
    
  
    # Process all bookings concurrently
    # tasks = [process_booking_geocoding(booking, semaphore) for booking in bookings_data]  
    # await asyncio.gather(*tasks)
  
    bookings_data = []
  
    for booking in updated_bookings:
        # Validate each booking using Pydantic
        try:
            bookings_data.append(Booking(**booking))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"Invalid booking data: {str(e)}")
  
  
    
    result = optimize_routes(bookings_data)
    
    with open('optimized_routes_response.json',"w") as f:
        json.dump(result, f, indent=2)
	
  
    return bookings_data, result
    


updated_bookings = [
   {
		"id": "15706825",
		"customer": "Langelaar",
		"passengers": 2,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T07:21:00+00:00",
		"pickupAddress": "Prinses Margrietstraat 15 3314NP Dordrecht",
		"deliveryTime": "2025-07-22T08:30:00+00:00",
		"deliveryAddress": "Catsheuvel 37 2517JZ 's-Gravenhage",
		"pickup": {
			"latitude": 51.7991788,
			"longitude": 4.6682264
		},
		"delivery": {
			"latitude": 52.091497,
			"longitude": 4.2807814
		}
	},
	{
		"id": "15753873",
		"customer": "van der Laan",
		"passengers": 3,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T06:36:00+00:00",
		"pickupAddress": "Fabritiusstraat 65 2612HN Delft",
		"deliveryTime": "2025-07-22T08:15:00+00:00",
		"deliveryAddress": "Europalaan 1 5171KW Kaatsheuvel",
		"pickup": {
			"latitude": 52.0165793,
			"longitude": 4.363576
		},
		"delivery": {
			"latitude": 51.6521166,
			"longitude": 5.0497462
		}
	},
	{
		"id": "15777469",
		"customer": "Karreman",
		"passengers": 2,
  		"wheelchairs": 0,
		"pickupTime": "2025-07-22T07:00:00+00:00",
		"pickupAddress": "De Mirandastraat 7 2622BN Delft",
		"deliveryTime": "2025-07-22T08:39:00+00:00",
		"deliveryAddress": "Oude Drift 1 1251BS Laren (nh)",
		"pickup": {
			"latitude": 51.98444540000001,
			"longitude": 4.3510275
		},
		"delivery": {
			"latitude": 52.2593045,
			"longitude": 5.2214955
		}
	},
	{
		"id": "15777483",
		"customer": "Karreman",
		"passengers": 2,
  		"wheelchairs": 0,
		"pickupTime": "2025-07-22T13:00:00+00:00",
		"pickupAddress": "Oude Drift 1 1251BS Laren (nh)",
		"deliveryTime": "2025-07-22T14:40:00+00:00",
		"deliveryAddress": "De Mirandastraat 7 2622BN Delft",
		"pickup": {
			"latitude": 52.2593045,
			"longitude": 5.2214955
		},
		"delivery": {
			"latitude": 51.98444540000001,
			"longitude": 4.3510275
		}
	},
	{
		"id": "15905581",
		"customer": "Bleij-Bogaart",
		"passengers": 1,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T19:00:00+00:00",
		"pickupAddress": "Veerkade 126 1357PP Almere",
		"deliveryTime": "2025-07-22T21:35:00+00:00",
		"deliveryAddress": "Mariaplein 29 4702GM Roosendaal",
		"pickup": {
			"latitude": 52.3322435,
			"longitude": 5.2222247
		},
		"delivery": {
			"latitude": 51.5334235,
			"longitude": 4.4731913
		}
	},
	{
		"id": "15917568",
		"customer": "Stoel-Janssen",
		"passengers": 1,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T08:44:00+00:00",
		"pickupAddress": "'s-Heerenbergstraat 4 2241PG Wassenaar",
		"deliveryTime": "2025-07-22T11:30:00+00:00",
		"deliveryAddress": "Aalsterweg 322 5644RL Eindhoven",
		"pickup": {
			"latitude": 52.1484862,
			"longitude": 4.4012445
		},
		"delivery": {
			"latitude": 51.4065707,
			"longitude": 5.4785318
		}
	},
	{
		"id": "15921267",
		"customer": "van Nieuwland - Michels",
		"passengers": 1,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T10:30:00+00:00",
		"pickupAddress": "Hoge Maasdijk 42 b 4281NG Andel",
		"deliveryTime": "2025-07-22T12:05:00+00:00",
		"deliveryAddress": "Ekenrooisestraat 6 5583TA Waalre",
		"pickup": {
			"latitude": 51.7853121,
			"longitude": 5.0578861
		},
		"delivery": {
			"latitude": 51.3945775,
			"longitude": 5.4852162
		}
	},
	{
		"id": "15926446",
		"customer": "van Oord-Henskes",
		"passengers": 1,
		"wheelchairs": 0,
		"pickupTime": "2025-07-22T17:30:00+00:00",
		"pickupAddress": "Tuindersvaart 66 2614SK Delft",
		"deliveryTime": "2025-07-22T19:07:00+00:00",
		"deliveryAddress": "Beresteinseweg 12 1243LC 's-Graveland",
		"pickup": {
			"latitude": 52.009983,
			"longitude": 4.328933
		},
		"delivery": {
			"latitude": 52.2246773,
			"longitude": 5.1247472
		}
	},
	{
		"id": "15927173",
		"customer": "Alkemade",
		"passengers": 0,
		"wheelchairs": 1,
		"pickupTime": "2025-07-22T16:30:00+00:00",
		"pickupAddress": "Fazantstraat 2 2225PN Katwijk",
		"deliveryTime": "2025-07-22T18:55:00+00:00",
		"deliveryAddress": "Sint Oloflaan 1 034 5037EP Tilburg",
		"pickup": {
			"latitude": 52.198905,
			"longitude": 4.4031635
		},
		"delivery": {
			"latitude": 51.5578993,
			"longitude": 5.0613264
		}
	},
	{
		"id": "15927970",
		"customer": "Jozen-van Dorst",
		"passengers": 0,
		"wheelchairs": 2,
		"pickupTime": "2025-07-22T16:00:00+00:00",
		"pickupAddress": "Zaagmolenstraat 47 2265XG Leidschendam",
		"deliveryTime": "2025-07-22T17:36:00+00:00",
		"deliveryAddress": "Overakkerstraat 105 D10 4834XK Breda",
		"pickup": {
			"latitude": 52.082195,
			"longitude": 4.398533
		},
		"delivery": {
			"latitude": 51.570304,
			"longitude": 4.7999278
		}
	},

	{
		"id": "15928611",
		"customer": "Daamen-Thakoerdin",
		"passengers": 2,
		"pickupTime": "2025-07-22T12:00:00+00:00",
		"pickupAddress": "Cornelis Ouwejanstraat 11 1506SX Zaandam",
		"deliveryTime": "2025-07-22T13:32:00+00:00",
		"deliveryAddress": "Hooghalenstraat 7 2545WJ 's-Gravenhage",
		"pickup": {
			"latitude": 52.422587,
			"longitude": 4.8263963
		},
		"delivery": {
			"latitude": 52.0516363,
			"longitude": 4.271618
		}
	},
	{
		"id": "15933449",
		"customer": "FRANKEN",
		"passengers": 1,
		"pickupTime": "2025-07-22T17:00:00+00:00",
		"pickupAddress": "Akkerwinde 49 2906XC Capelle aan den IJssel",
		"deliveryTime": "2025-07-22T18:46:00+00:00",
		"deliveryAddress": "Konijnenberg 4 5074MR Biezenmortel",
		"pickup": {
			"latitude": 51.9303145,
			"longitude": 4.5655448
		},
		"delivery": {
			"latitude": 51.6170363,
			"longitude": 5.1890157
		}
	},
	{
		"id": "15935239",
		"customer": "Khairoun",
		"passengers": 1,
		"pickupTime": "2025-07-22T15:00:00+00:00",
		"pickupAddress": "Albinusdreef 2 2333ZA Leiden",
		"deliveryTime": "2025-07-22T15:46:00+00:00",
		"deliveryAddress": "Westhovenplein 21 2532BA 's-Gravenhage",
		"pickup": {
			"latitude": 52.1655287,
			"longitude": 4.4782245
		},
		"delivery": {
			"latitude": 52.0464851,
			"longitude": 4.2961581
		}
	},
	{
		"id": "15935855",
		"customer": "Post-Franken",
		"passengers": 2,
		"pickupTime": "2025-07-22T12:15:00+00:00",
		"pickupAddress": "Kerkbrink 1 3851MB Ermelo",
		"deliveryTime": "2025-07-22T14:31:00+00:00",
		"deliveryAddress": "Koetlaan 86 2625KT Delft",
		"pickup": {
			"latitude": 52.2991106,
			"longitude": 5.6306227
		},
		"delivery": {
			"latitude": 51.9889332,
			"longitude": 4.337281
		}
	},
	{
		"id": "15937104",
		"customer": "Kooper-van der Geld",
		"passengers": 1,
		"pickupTime": "2025-07-22T08:30:00+00:00",
		"pickupAddress": "Cornelis Jolstraat 24 a 2584ES 's-Gravenhage",
		"deliveryTime": "2025-07-22T10:49:00+00:00",
		"deliveryAddress": "Koeweg 16 6731SJ Otterlo",
		"pickup": {
			"latitude": 52.1036477,
			"longitude": 4.2846122
		},
		"delivery": {
			"latitude": 52.094929,
			"longitude": 5.7634908
		}
	},
	{
		"id": "15937275",
		"customer": "KAPTIJN- MAYHEW",
		"passengers": 1,
		"pickupTime": "2025-07-22T20:45:00+00:00",
		"pickupAddress": "Conradstraat 10 3013AP Rotterdam",
		"deliveryTime": "2025-07-22T22:30:00+00:00",
		"deliveryAddress": "Maartenshof 44 4695HV Sint-Maartensdijk",
		"pickup": {
			"latitude": 51.92334289999999,
			"longitude": 4.469163099999999
		},
		"delivery": {
			"latitude": 51.5512811,
			"longitude": 4.0743027
		}
	},

]

updated_bookings_1 = [
	{
		"id": "15706825",
		"customer": "Langelaar",
		"passengers": 2,
		"pickupTime": "2025-07-22T07:21:00+00:00",
		"pickupAddress": "Prinses Margrietstraat 15 3314NP Dordrecht",
		"deliveryTime": "2025-07-22T08:30:00+00:00",
		"deliveryAddress": "Catsheuvel 37 2517JZ 's-Gravenhage",
		"pickup": {
			"latitude": 51.7991788,
			"longitude": 4.6682264
		},
		"delivery": {
			"latitude": 52.091497,
			"longitude": 4.2807814
		}
	},
	{
		"id": "15753873",
		"customer": "van der Laan",
		"passengers": 3,
		"pickupTime": "2025-07-22T06:36:00+00:00",
		"pickupAddress": "Fabritiusstraat 65 2612HN Delft",
		"deliveryTime": "2025-07-22T08:15:00+00:00",
		"deliveryAddress": "Europalaan 1 5171KW Kaatsheuvel",
		"pickup": {
			"latitude": 52.0165793,
			"longitude": 4.363576
		},
		"delivery": {
			"latitude": 51.6521166,
			"longitude": 5.0497462
		}
	},
	{
		"id": "15777469",
		"customer": "Karreman",
		"passengers": 2,
		"pickupTime": "2025-07-22T07:00:00+00:00",
		"pickupAddress": "De Mirandastraat 7 2622BN Delft",
		"deliveryTime": "2025-07-22T08:39:00+00:00",
		"deliveryAddress": "Oude Drift 1 1251BS Laren (nh)",
		"pickup": {
			"latitude": 51.98444540000001,
			"longitude": 4.3510275
		},
		"delivery": {
			"latitude": 52.2593045,
			"longitude": 5.2214955
		}
	},
	{
		"id": "15777483",
		"customer": "Karreman",
		"passengers": 2,
		"pickupTime": "2025-07-22T13:00:00+00:00",
		"pickupAddress": "Oude Drift 1 1251BS Laren (nh)",
		"deliveryTime": "2025-07-22T14:40:00+00:00",
		"deliveryAddress": "De Mirandastraat 7 2622BN Delft",
		"pickup": {
			"latitude": 52.2593045,
			"longitude": 5.2214955
		},
		"delivery": {
			"latitude": 51.98444540000001,
			"longitude": 4.3510275
		}
	},
	{
		"id": "15905581",
		"customer": "Bleij-Bogaart",
		"passengers": 1,
		"pickupTime": "2025-07-22T19:00:00+00:00",
		"pickupAddress": "Veerkade 126 1357PP Almere",
		"deliveryTime": "2025-07-22T21:35:00+00:00",
		"deliveryAddress": "Mariaplein 29 4702GM Roosendaal",
		"pickup": {
			"latitude": 52.3322435,
			"longitude": 5.2222247
		},
		"delivery": {
			"latitude": 51.5334235,
			"longitude": 4.4731913
		}
	},
	{
		"id": "15917568",
		"customer": "Stoel-Janssen",
		"passengers": 1,
		"pickupTime": "2025-07-22T08:44:00+00:00",
		"pickupAddress": "'s-Heerenbergstraat 4 2241PG Wassenaar",
		"deliveryTime": "2025-07-22T11:30:00+00:00",
		"deliveryAddress": "Aalsterweg 322 5644RL Eindhoven",
		"pickup": {
			"latitude": 52.1484862,
			"longitude": 4.4012445
		},
		"delivery": {
			"latitude": 51.4065707,
			"longitude": 5.4785318
		}
	},
	{
		"id": "15921267",
		"customer": "van Nieuwland - Michels",
		"passengers": 1,
		"pickupTime": "2025-07-22T10:30:00+00:00",
		"pickupAddress": "Hoge Maasdijk 42 b 4281NG Andel",
		"deliveryTime": "2025-07-22T12:05:00+00:00",
		"deliveryAddress": "Ekenrooisestraat 6 5583TA Waalre",
		"pickup": {
			"latitude": 51.7853121,
			"longitude": 5.0578861
		},
		"delivery": {
			"latitude": 51.3945775,
			"longitude": 5.4852162
		}
	},
	{
		"id": "15926446",
		"customer": "van Oord-Henskes",
		"passengers": 1,
		"pickupTime": "2025-07-22T17:30:00+00:00",
		"pickupAddress": "Tuindersvaart 66 2614SK Delft",
		"deliveryTime": "2025-07-22T19:07:00+00:00",
		"deliveryAddress": "Beresteinseweg 12 1243LC 's-Graveland",
		"pickup": {
			"latitude": 52.009983,
			"longitude": 4.328933
		},
		"delivery": {
			"latitude": 52.2246773,
			"longitude": 5.1247472
		}
	},
	{
		"id": "15927173",
		"customer": "Alkemade",
		"passengers": 1,
		"pickupTime": "2025-07-22T16:30:00+00:00",
		"pickupAddress": "Fazantstraat 2 2225PN Katwijk",
		"deliveryTime": "2025-07-22T18:55:00+00:00",
		"deliveryAddress": "Sint Oloflaan 1 034 5037EP Tilburg",
		"pickup": {
			"latitude": 52.198905,
			"longitude": 4.4031635
		},
		"delivery": {
			"latitude": 51.5578993,
			"longitude": 5.0613264
		}
	},
	{
		"id": "15927970",
		"customer": "Jozen-van Dorst",
		"passengers": 1,
		"pickupTime": "2025-07-22T16:00:00+00:00",
		"pickupAddress": "Zaagmolenstraat 47 2265XG Leidschendam",
		"deliveryTime": "2025-07-22T17:36:00+00:00",
		"deliveryAddress": "Overakkerstraat 105 D10 4834XK Breda",
		"pickup": {
			"latitude": 52.082195,
			"longitude": 4.398533
		},
		"delivery": {
			"latitude": 51.570304,
			"longitude": 4.7999278
		}
	},
	{
		"id": "15928611",
		"customer": "Daamen-Thakoerdin",
		"passengers": 2,
		"pickupTime": "2025-07-22T12:00:00+00:00",
		"pickupAddress": "Cornelis Ouwejanstraat 11 1506SX Zaandam",
		"deliveryTime": "2025-07-22T13:32:00+00:00",
		"deliveryAddress": "Hooghalenstraat 7 2545WJ 's-Gravenhage",
		"pickup": {
			"latitude": 52.422587,
			"longitude": 4.8263963
		},
		"delivery": {
			"latitude": 52.0516363,
			"longitude": 4.271618
		}
	},
	{
		"id": "15933449",
		"customer": "FRANKEN",
		"passengers": 1,
		"pickupTime": "2025-07-22T17:00:00+00:00",
		"pickupAddress": "Akkerwinde 49 2906XC Capelle aan den IJssel",
		"deliveryTime": "2025-07-22T18:46:00+00:00",
		"deliveryAddress": "Konijnenberg 4 5074MR Biezenmortel",
		"pickup": {
			"latitude": 51.9303145,
			"longitude": 4.5655448
		},
		"delivery": {
			"latitude": 51.6170363,
			"longitude": 5.1890157
		}
	},
	{
		"id": "15935239",
		"customer": "Khairoun",
		"passengers": 1,
		"pickupTime": "2025-07-22T15:00:00+00:00",
		"pickupAddress": "Albinusdreef 2 2333ZA Leiden",
		"deliveryTime": "2025-07-22T15:46:00+00:00",
		"deliveryAddress": "Westhovenplein 21 2532BA 's-Gravenhage",
		"pickup": {
			"latitude": 52.1655287,
			"longitude": 4.4782245
		},
		"delivery": {
			"latitude": 52.0464851,
			"longitude": 4.2961581
		}
	},
	{
		"id": "15935855",
		"customer": "Post-Franken",
		"passengers": 2,
		"pickupTime": "2025-07-22T12:15:00+00:00",
		"pickupAddress": "Kerkbrink 1 3851MB Ermelo",
		"deliveryTime": "2025-07-22T14:31:00+00:00",
		"deliveryAddress": "Koetlaan 86 2625KT Delft",
		"pickup": {
			"latitude": 52.2991106,
			"longitude": 5.6306227
		},
		"delivery": {
			"latitude": 51.9889332,
			"longitude": 4.337281
		}
	},
	{
		"id": "15937104",
		"customer": "Kooper-van der Geld",
		"passengers": 1,
		"pickupTime": "2025-07-22T08:30:00+00:00",
		"pickupAddress": "Cornelis Jolstraat 24 a 2584ES 's-Gravenhage",
		"deliveryTime": "2025-07-22T10:49:00+00:00",
		"deliveryAddress": "Koeweg 16 6731SJ Otterlo",
		"pickup": {
			"latitude": 52.1036477,
			"longitude": 4.2846122
		},
		"delivery": {
			"latitude": 52.094929,
			"longitude": 5.7634908
		}
	},
	{
		"id": "15937275",
		"customer": "KAPTIJN- MAYHEW",
		"passengers": 1,
		"pickupTime": "2025-07-22T20:45:00+00:00",
		"pickupAddress": "Conradstraat 10 3013AP Rotterdam",
		"deliveryTime": "2025-07-22T22:30:00+00:00",
		"deliveryAddress": "Maartenshof 44 4695HV Sint-Maartensdijk",
		"pickup": {
			"latitude": 51.92334289999999,
			"longitude": 4.469163099999999
		},
		"delivery": {
			"latitude": 51.5512811,
			"longitude": 4.0743027
		}
	},
	{
		"id": "15938346",
		"customer": "Rozemond",
		"passengers": 1,
		"pickupTime": "2025-07-22T09:00:00+00:00",
		"pickupAddress": "Willem van Arkellaan 3 4205GT Gorinchem",
		"deliveryTime": "2025-07-22T09:58:00+00:00",
		"deliveryAddress": "Boerhaavelaan 99 3552CW Utrecht",
		"pickup": {
			"latitude": 51.84185979999999,
			"longitude": 4.970403
		},
		"delivery": {
			"latitude": 52.106185,
			"longitude": 5.098959
		}
	},
	{
		"id": "15938788",
		"customer": "VAN BLIJDERVEEN",
		"passengers": 2,
		"pickupTime": "2025-07-22T18:30:00+00:00",
		"pickupAddress": "Jeroen Boschlaan 34 5056CW Berkel-Enschot",
		"deliveryTime": "2025-07-22T20:06:00+00:00",
		"deliveryAddress": "Tusculum 15 6674DM Herveld",
		"pickup": {
			"latitude": 51.581965,
			"longitude": 5.137841799999999
		},
		"delivery": {
			"latitude": 51.9084233,
			"longitude": 5.742770399999999
		}
	},
	{
		"id": "15940233",
		"customer": "van Andel",
		"passengers": 1,
		"pickupTime": "2025-07-22T12:45:00+00:00",
		"pickupAddress": "Brederodeweg 23 5283HA Boxtel",
		"deliveryTime": "2025-07-22T13:53:00+00:00",
		"deliveryAddress": "Schapendonk 94 4942CG Raamsdonksveer",
		"pickup": {
			"latitude": 51.5874367,
			"longitude": 5.3316791
		},
		"delivery": {
			"latitude": 51.70524030000001,
			"longitude": 4.8771583
		}
	},
	{
		"id": "15940285",
		"customer": "van Anker",
		"passengers": 2,
		"pickupTime": "2025-07-22T16:00:00+00:00",
		"pickupAddress": "Koningin Wilhelmina Boulevard 4 2202GR Noordwijk (zh)",
		"deliveryTime": "2025-07-22T18:19:00+00:00",
		"deliveryAddress": "mgr. Bekkersplein 4 5328CK Rossum (ge)",
		"pickup": {
			"latitude": 52.2442961,
			"longitude": 4.4299259
		},
		"delivery": {
			"latitude": 51.8024451,
			"longitude": 5.3303696
		}
	},
	{
		"id": "15941499",
		"customer": "Winkelmolen-Jeijsman",
		"passengers": 1,
		"pickupTime": "2025-07-22T09:45:00+00:00",
		"pickupAddress": "Molenstraat 163 5262EC Vught",
		"deliveryTime": "2025-07-22T11:15:00+00:00",
		"deliveryAddress": "Planetenlaan 188 3318JM Dordrecht",
		"pickup": {
			"latitude": 51.646507,
			"longitude": 5.285388999999999
		},
		"delivery": {
			"latitude": 51.78575,
			"longitude": 4.675961
		}
	},
	{
		"id": "15942314",
		"customer": "van Diepen-Verbij",
		"passengers": 1,
		"pickupTime": "2025-07-22T08:30:00+00:00",
		"pickupAddress": "Grotiusplantsoen 2 5121TR Rijen",
		"deliveryTime": "2025-07-22T10:53:00+00:00",
		"deliveryAddress": "Faunastraat 120 1531WJ Wormer",
		"pickup": {
			"latitude": 51.59251459999999,
			"longitude": 4.910601199999999
		},
		"delivery": {
			"latitude": 52.4993934,
			"longitude": 4.8129336
		}
	},
	{
		"id": "15942621",
		"customer": "Bakkers",
		"passengers": 1,
		"pickupTime": "2025-07-22T14:00:00+00:00",
		"pickupAddress": "Indus 62 3328ND Dordrecht",
		"deliveryTime": "2025-07-22T15:00:00+00:00",
		"deliveryAddress": "De Vloot 69 B 3144PC Maassluis",
		"pickup": {
			"latitude": 51.7793893,
			"longitude": 4.6704964
		},
		"delivery": {
			"latitude": 51.92965,
			"longitude": 4.244866
		}
	},
	{
		"id": "15942849",
		"customer": "Tulgur",
		"passengers": 1,
		"pickupTime": "2025-07-22T08:30:00+00:00",
		"pickupAddress": "Sperwerhorst 125 3815AR Amersfoort",
		"deliveryTime": "2025-07-22T10:13:00+00:00",
		"deliveryAddress": "Sweelinckstraat 10 5144VB Waalwijk",
		"pickup": {
			"latitude": 52.1706278,
			"longitude": 5.4035236
		},
		"delivery": {
			"latitude": 51.67724399999999,
			"longitude": 5.0644297
		}
	},
	{
		"id": "15942899",
		"customer": "de Winter",
		"passengers": 2,
		"pickupTime": "2025-07-22T20:00:00+00:00",
		"pickupAddress": "Lindestraat 7 a 6096BW Grathem",
		"deliveryTime": "2025-07-22T22:53:00+00:00",
		"deliveryAddress": "Rechter Rottekade 209 3032XD Rotterdam",
		"pickup": {
			"latitude": 51.1925869,
			"longitude": 5.856738200000001
		},
		"delivery": {
			"latitude": 51.928529,
			"longitude": 4.483978
		}
	},
	{
		"id": "15944841",
		"customer": "Zeewijk",
		"passengers": 1,
		"pickupTime": "2025-07-22T11:00:00+00:00",
		"pickupAddress": "Markt 129 3351PA Papendrecht",
		"deliveryTime": "2025-07-22T11:46:00+00:00",
		"deliveryAddress": "Aveling 227 3193LE Hoogvliet Rotterdam",
		"pickup": {
			"latitude": 51.827457,
			"longitude": 4.683224399999999
		},
		"delivery": {
			"latitude": 51.8673097,
			"longitude": 4.3526488
		}
	}
]