import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class WeatherUnlockedFetcher:
    BASE_URL = "https://api.weatherunlocked.com/api/resortforecast"
    
    def __init__(self):
        self.app_id = settings.weather_unlocked_app_id
        self.api_key = settings.weather_unlocked_api_key
        
    async def fetch_resort_data(self, resort_id: str) -> Optional[Dict]:
        """Fetch weather data for a specific resort."""
        if not self.app_id or not self.api_key:
            logger.error("Weather Unlocked credentials not configured. Check .env file.")
            return None
            
        headers = {
            "Accept": "application/json"
        }
        
        logger.info(f"Fetching data for resort {resort_id}")
        logger.debug(f"Using credentials - App ID: {self.app_id}, API Key: {self.api_key}")
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/{resort_id}?app_id={self.app_id}&app_key={self.api_key}"
            logger.debug(f"Making request to: {url}")
            logger.debug(f"Headers: {headers}")
            
            try:
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    logger.debug(f"Response status: {response.status}")
                    logger.debug(f"Response headers: {response.headers}")
                    logger.debug(f"Response body: {response_text}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"Successfully fetched data for resort {resort_id}")
                            return data
                        except Exception as e:
                            logger.error(f"Failed to parse JSON response for resort {resort_id}: {str(e)}")
                            return None
                    else:
                        logger.error(f"Failed to fetch resort data for {resort_id}: Status {response.status}, Response: {response_text}")
                        return None
            except Exception as e:
                logger.error(f"Exception while fetching resort {resort_id}: {str(e)}")
                return None

    def process_resort_data(self, resort_id: str, data: Dict) -> Dict:
        """Process raw resort data into standardized format."""
        return {
            'resort_name': data.get('name', ''),
            'state': data.get('region', '').split(',')[-1].strip(),
            'timestamp': datetime.now(),
            'snow_depth': data.get('snow_depth', 0),
            'new_snow_24h': data.get('snow_last_24h', 0),
            'new_snow_72h': data.get('snow_last_72h', 0),
            'new_snow_7d': data.get('snow_last_7d', 0),
            'elevation': data.get('base_elevation_ft', 0),
            'temperature': data.get('base_temp_f', None),
            'data_source': 'WeatherUnlocked'
        }

    # Common US ski resort IDs from Weather Unlocked
    US_SKI_RESORTS = [
        {'id': '333012', 'name': 'Vail', 'state': 'Colorado'},
        {'id': '333009', 'name': 'Aspen Snowmass', 'state': 'Colorado'},
        {'id': '333020', 'name': 'Park City', 'state': 'Utah'},
        {'id': '333275', 'name': 'Mammoth Mountain', 'state': 'California'},
        {'id': '333024', 'name': 'Breckenridge', 'state': 'Colorado'},
        {'id': '333011', 'name': 'Steamboat', 'state': 'Colorado'},
        {'id': '333021', 'name': 'Alta', 'state': 'Utah'},
        {'id': '333023', 'name': 'Jackson Hole', 'state': 'Wyoming'},
        {'id': '333276', 'name': 'Squaw Valley', 'state': 'California'},
        {'id': '333277', 'name': 'Heavenly', 'state': 'California'},
        {'id': '333015', 'name': 'Big Sky', 'state': 'Montana'},
        {'id': '333278', 'name': 'Killington', 'state': 'Vermont'},
        {'id': '333279', 'name': 'Stowe', 'state': 'Vermont'},
        {'id': '333280', 'name': 'Sugarloaf', 'state': 'Maine'},
        {'id': '333281', 'name': 'Whiteface', 'state': 'New York'}
    ]

    async def fetch_all_resorts(self) -> List[Dict]:
        """Fetch weather data for all US resorts."""
        if not self.app_id or not self.api_key:
            logger.error("Weather Unlocked API credentials not configured")
            return []
            
        logger.info(f"Starting to fetch data for {len(self.US_SKI_RESORTS)} US ski resorts")
        
        tasks = []
        for resort in self.US_SKI_RESORTS:
            tasks.append(self.fetch_resort_data(resort['id']))
        
        results = await asyncio.gather(*tasks)
        processed_results = []
        
        for resort_info, result in zip(self.US_SKI_RESORTS, results):
            if result:
                try:
                    # Merge resort info with API response
                    result.update({
                        'name': resort_info['name'],
                        'region': f"USA, {resort_info['state']}"
                    })
                    processed_data = self.process_resort_data(resort_info['id'], result)
                    if processed_data:
                        processed_results.append(processed_data)
                        logger.info(f"Successfully processed data for {resort_info['name']}")
                    else:
                        logger.warning(f"Failed to process data for {resort_info['name']}")
                except Exception as e:
                    logger.error(f"Error processing resort {resort_info['name']}: {str(e)}")
                    continue
        
        logger.info(f"Successfully fetched and processed data for {len(processed_results)} resorts")
        return processed_results
