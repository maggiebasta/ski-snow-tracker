from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import logging

from .database import get_db, init_db
from .models.weather import SnowReport
from .data_fetchers.snotel import SnotelDataFetcher
from .data_fetchers.weather_unlocked import WeatherUnlockedFetcher

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

# Configure all loggers
for name in ['app', 'app.data_fetchers', 'app.data_fetchers.snotel', 'app.data_fetchers.weather_unlocked']:
    logging.getLogger(name).setLevel(logging.DEBUG)
    # Add a stream handler if none exists
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize database tables
init_db()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

from fastapi import HTTPException
from typing import List
from pydantic import BaseModel

class ResortSnowReport(BaseModel):
    resort_name: str
    state: str
    new_snow_7d: float
    snow_depth: float
    elevation: float
    temperature: float | None
    data_source: str
    timestamp: str | None

@app.get("/api/snow/top-resorts", response_model=List[ResortSnowReport])
async def get_top_snow_resorts(
    db: Session = Depends(get_db),
    min_elevation: float | None = None,
    state: str | None = None,
    limit: int = 10
):
    """
    Get top ski resorts by new snow in the past week.
    
    Parameters:
    - min_elevation: Optional minimum elevation in feet
    - state: Optional state filter (e.g., 'CO', 'UT')
    - limit: Maximum number of results (default: 10)
    """
    try:
        # Build query
        query = db.query(SnowReport)\
            .filter(SnowReport.timestamp >= datetime.now() - timedelta(days=7))
        
        # Apply filters
        if min_elevation:
            query = query.filter(SnowReport.elevation >= min_elevation)
        if state:
            query = query.filter(SnowReport.state == state.upper())
            
        # Get results
        top_resorts = query\
            .order_by(SnowReport.new_snow_7d.desc())\
            .limit(min(limit, 50))\
            .all()  # Cap at 50 results
        
        if not top_resorts:
            raise HTTPException(
                status_code=404,
                detail="No snow reports found matching the criteria"
            )
        
        # Convert to response model
        return [
            ResortSnowReport(
                resort_name=resort.resort_name,
                state=resort.state,
                new_snow_7d=float(resort.new_snow_7d) if resort.new_snow_7d else 0.0,
                snow_depth=float(resort.snow_depth) if resort.snow_depth else 0.0,
                elevation=float(resort.elevation) if resort.elevation else 0.0,
                temperature=float(resort.temperature) if resort.temperature else None,
                data_source=resort.data_source,
                timestamp=resort.timestamp.isoformat() if resort.timestamp else None
            )
            for resort in top_resorts
        ]
    except Exception as e:
        logger.error(f"Error fetching top resorts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching snow reports"
        )

from pydantic import BaseModel
from typing import List, Dict

class SnowDataResponse(BaseModel):
    status: str
    message: str
    resort_count: int
    errors: List[Dict[str, str]] = []

@app.post("/api/snow/fetch", response_model=SnowDataResponse)
async def fetch_snow_data(db: Session = Depends(get_db)):
    """
    Fetch latest snow data from all sources.
    
    Returns:
    - status: success/warning/error
    - message: Human-readable status message
    - resort_count: Number of successfully processed resorts
    - errors: List of errors encountered during processing
    """
    errors = []
    try:
        # Fetch data from all sources
        snotel_fetcher = SnotelDataFetcher()
        weather_unlocked_fetcher = WeatherUnlockedFetcher()
        
        # Gather data from both sources
        snotel_data = await snotel_fetcher.fetch_all_snow_data()
        weather_unlocked_data = await weather_unlocked_fetcher.fetch_all_resorts()
        
        # Combine data from both sources
        snow_data = snotel_data + weather_unlocked_data
        
        if not snow_data:
            return SnowDataResponse(
                status="warning",
                message="No snow data was retrieved from any source",
                resort_count=0
            )
        
        # Store in database
        new_reports = 0
        for data in snow_data:
            try:
                # Validate required fields
                if not all(k in data for k in ['resort_name', 'state', 'snow_depth']):
                    errors.append({
                        'resort': data.get('resort_name', 'Unknown'),
                        'error': 'Missing required fields'
                    })
                    continue
                
                # Validate data types
                if not isinstance(data.get('snow_depth'), (int, float)):
                    errors.append({
                        'resort': data['resort_name'],
                        'error': 'Invalid snow depth value'
                    })
                    continue
                
                snow_report = SnowReport(**data)
                db.add(snow_report)
                new_reports += 1
            except Exception as e:
                errors.append({
                    'resort': data.get('resort_name', 'Unknown'),
                    'error': str(e)
                })
                continue
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
        
        status = "success" if new_reports > 0 else "warning"
        return SnowDataResponse(
            status=status,
            message=f"Processed {new_reports} resorts" + (f" with {len(errors)} errors" if errors else ""),
            resort_count=new_reports,
            errors=errors
        )
    except Exception as e:
        logger.error(f"Error in fetch_snow_data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
