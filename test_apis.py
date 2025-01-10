import asyncio
import logging
from app.data_fetchers.snotel import SnotelDataFetcher
from app.data_fetchers.weather_unlocked import WeatherUnlockedFetcher

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_snotel():
    print("\n=== Testing SNOTEL API ===")
    fetcher = SnotelDataFetcher()
    
    print("\nFetching stations...")
    stations = await fetcher.fetch_stations()
    print(f"Found {len(stations)} stations")
    if stations:
        print("First station:", stations[0])
        
        print("\nFetching snow data for first station...")
        snow_data = await fetcher.fetch_snow_data(stations[0]['stationTriplet'])
        print("Snow data:", snow_data)
        
        print("\nTesting full pipeline with first 3 stations...")
        test_stations = stations[:3]
        processed_data = []
        for station in test_stations:
            result = await fetcher.process_station_data(station)
            if result:
                processed_data.append(result)
                print(f"\nProcessed data for {station['name']}:")
                print(f"Snow depth: {result['snow_depth']} inches")
                print(f"New snow (24h/72h/7d): {result['new_snow_24h']}/{result['new_snow_72h']}/{result['new_snow_7d']} inches")

async def test_weather_unlocked():
    print("\n=== Testing Weather Unlocked API ===")
    fetcher = WeatherUnlockedFetcher()
    
    print("\nFetching first resort...")
    first_resort = fetcher.US_SKI_RESORTS[0]
    print(f"Testing with resort: {first_resort['name']} (ID: {first_resort['id']})")
    
    resort_data = await fetcher.fetch_resort_data(first_resort['id'])
    print("Resort data:", resort_data)

async def main():
    print("Starting API tests...")
    
    print("\nTesting SNOTEL API...")
    await test_snotel()
    
    print("\nTesting Weather Unlocked API...")
    await test_weather_unlocked()

if __name__ == "__main__":
    asyncio.run(main())
