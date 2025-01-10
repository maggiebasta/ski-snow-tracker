import aiohttp
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import logging
import xmltodict

logger = logging.getLogger(__name__)

class SnotelDataFetcher:
    # SNOTEL API Documentation: https://www.nrcs.usda.gov/wps/portal/wcc/home/dataAccessHelp/webService/webServiceReference
    BASE_URL = "https://wcc.sc.egov.usda.gov/awdbWebService/services"
    
    async def fetch_stations(self) -> List[Dict]:
        """Fetch all SNOTEL stations."""
        logger.info("Fetching SNOTEL stations...")
        
        # SOAP request for getStations
        # Reference: https://www.nrcs.usda.gov/wps/portal/wcc/home/dataAccessHelp/webService/webServiceReference
        soap_request = """<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header/>
            <soap:Body>
                <awdb:getStations xmlns:awdb="http://www.wcc.nrcs.usda.gov/ns/awdbWebService">
                    <stationIds></stationIds>
                    <elementCds>SNWD</elementCds>
                    <ordinals>1</ordinals>
                    <heightDepths></heightDepths>
                    <networkCds>SNTL</networkCds>
                </awdb:getStations>
            </soap:Body>
        </soap:Envelope>
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                url = self.BASE_URL
                logger.info(f"Making SOAP request to: {url}")
                headers = {
                    'Content-Type': 'text/xml;charset=UTF-8',
                    'SOAPAction': ''
                }
                
                async with session.post(url, data=soap_request.strip(), headers=headers) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        logger.debug(f"Received SOAP response: {response_text}")
                        
                        # Parse XML response
                        response_dict = xmltodict.parse(response_text)
                        logger.debug(f"Parsed XML response: {response_dict}")
                        
                        # Extract stations from SOAP response
                        try:
                            stations_data = response_dict['soap:Envelope']['soap:Body']['ns2:getStationsResponse']['return']
                            if not isinstance(stations_data, list):
                                stations_data = [stations_data]
                                
                            stations = []
                            for station_id in stations_data:
                                # Parse station ID format "CODE:STATE:TYPE"
                                try:
                                    code, state, station_type = station_id.split(':')
                                    if station_type == 'SNTL':  # Only use SNOTEL stations
                                        stations.append({
                                            'name': f"SNOTEL Station {code}",
                                            'stationTriplet': station_id,
                                            'state': state,
                                            'elevation': 0  # We'll get this from getData response
                                        })
                                except ValueError as e:
                                    logger.warning(f"Failed to parse station ID {station_id}: {str(e)}")
                                    continue
                            
                            logger.info(f"Found {len(stations)} SNOTEL stations above 6000ft")
                            return stations
                        except (KeyError, ValueError) as e:
                            logger.error(f"Error parsing SNOTEL stations response: {str(e)}")
                            return []
                    else:
                        response_text = await response.text()
                        logger.error(f"Failed to fetch stations: Status {response.status}, Response: {response_text}")
                        return []
        except Exception as e:
            logger.error(f"Exception while fetching SNOTEL stations: {str(e)}")
            return []

    async def fetch_snow_data(self, station_id: str, days: int = 7) -> Dict:
        """Fetch snow data for a specific station for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # SOAP request for getData
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header/>
            <soap:Body>
                <awdb:getData xmlns:awdb="http://www.wcc.nrcs.usda.gov/ns/awdbWebService">
                    <stationTriplets>{station_id}</stationTriplets>
                    <elementCd>SNWD</elementCd>
                    <ordinal>1</ordinal>
                    <heightDepth></heightDepth>
                    <duration>DAILY</duration>
                    <getFlags>false</getFlags>
                    <beginDate>{start_date.strftime('%Y-%m-%d')}</beginDate>
                    <endDate>{end_date.strftime('%Y-%m-%d')}</endDate>
                    <alwaysReturnDailyFeb29>false</alwaysReturnDailyFeb29>
                </awdb:getData>
            </soap:Body>
        </soap:Envelope>
        """
        
        logger.debug(f"Fetching snow data for station {station_id} from {start_date} to {end_date}")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = self.BASE_URL
                headers = {
                    'Content-Type': 'text/xml;charset=UTF-8',
                    'SOAPAction': ''
                }
                
                async with session.post(url, data=soap_request.strip(), headers=headers) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        logger.debug(f"Received SOAP response for {station_id}: {response_text}")
                        
                        # Parse XML response
                        response_dict = xmltodict.parse(response_text)
                        logger.debug(f"Parsed XML response for {station_id}: {response_dict}")
                        
                        try:
                            # Extract values from SOAP response
                            # Check for SOAP fault first
                            if 'soap:Fault' in response_dict['soap:Envelope']['soap:Body']:
                                fault = response_dict['soap:Envelope']['soap:Body']['soap:Fault']['faultstring']
                                logger.error(f"SOAP Fault: {fault}")
                                return {}
                            
                            # If no fault, get the data
                            values_data = response_dict['soap:Envelope']['soap:Body']['ns2:getDataResponse']['return']
                            if not isinstance(values_data, list):
                                values_data = [values_data]
                                
                            # Extract dates and values from the first return element
                            data = values_data[0] if isinstance(values_data, list) else values_data
                            begin_date = datetime.strptime(data['beginDate'], '%Y-%m-%d %H:%M:%S')
                            values_list = data['values'] if isinstance(data['values'], list) else [data['values']]
                            
                            # Create daily timestamps
                            dates = [begin_date + timedelta(days=i) for i in range(len(values_list))]
                            
                            # Combine dates with values
                            values = []
                            for date, value in zip(dates, values_list):
                                values.append({
                                    'date': date.strftime('%Y-%m-%d'),
                                    'value': float(value)
                                })
                            
                            return {'values': values}
                        except (KeyError, ValueError) as e:
                            logger.error(f"Error parsing SNOTEL snow data response for {station_id}: {str(e)}")
                            return {}
                    else:
                        response_text = await response.text()
                        logger.error(f"Failed to fetch snow data for station {station_id}: Status {response.status}, Response: {response_text}")
                        return {}
        except Exception as e:
            logger.error(f"Exception while fetching snow data for station {station_id}: {str(e)}")
            return {}

    async def process_station_data(self, station: Dict) -> Dict | None:
        """Process snow data for a single station."""
        snow_data = await self.fetch_snow_data(station['stationTriplet'])
        if not snow_data:
            return None
            
        try:
            # Calculate snow changes
            df = pd.DataFrame(snow_data.get('values', []))
            if df.empty:
                logger.warning(f"No snow data available for station {station['stationTriplet']}")
                return None
                
            # Convert and clean data
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['value'])  # Remove any rows with invalid snow depths
            if df.empty:
                logger.warning(f"No valid snow depth measurements for station {station['stationTriplet']}")
                return None
                
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
                
            # Calculate changes, ensuring they're non-negative
            latest = df.iloc[-1]
            snow_24h = max(0, df.iloc[-1]['value'] - df.iloc[-2]['value'] if len(df) > 1 else 0)
            snow_72h = max(0, df.iloc[-1]['value'] - df.iloc[-4]['value'] if len(df) > 3 else 0)
            snow_7d = max(0, df.iloc[-1]['value'] - df.iloc[0]['value'] if len(df) > 6 else 0)
            
            # Validate snow depth is reasonable
            if latest['value'] < 0 or latest['value'] > 1000:  # Sanity check for snow depth
                logger.warning(f"Invalid snow depth ({latest['value']}) for station {station['stationTriplet']}")
                return None
        
            return {
                'resort_name': str(station['name']),
                'state': str(station['state']),
                'timestamp': datetime.now(),
                'snow_depth': float(latest['value']),
                'new_snow_24h': float(snow_24h),  # Already made non-negative above
                'new_snow_72h': float(snow_72h),
                'new_snow_7d': float(snow_7d),
                'elevation': float(station['elevation']) if station['elevation'] else 0.0,
                'temperature': None,  # Will be fetched separately
                'data_source': 'SNOTEL'
            }
        except Exception as e:
            logger.error(f"Error processing snow data for station {station['stationTriplet']}: {str(e)}")
            return None

    async def fetch_all_snow_data(self) -> List[Dict]:
        """Fetch and process snow data for all relevant stations."""
        stations = await self.fetch_stations()
        logger.info(f"Found {len(stations)} relevant SNOTEL stations")
        
        tasks = [self.process_station_data(station) for station in stations]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and sort by new snow in last 7 days
        valid_results = [r for r in results if r is not None]
        return sorted(valid_results, key=lambda x: x['new_snow_7d'], reverse=True)
