# Ski Snow Tracker

Data pipeline for tracking snow conditions at US ski resorts using SNOTEL and Weather Unlocked data, with DBT transformations and Supabase PostgreSQL backend.

## Features
- Fetches snow data from SNOTEL stations across the US
- Integrates with Weather Unlocked API for resort-specific conditions
- Uses DBT for data transformations and analytics
- Stores data in Supabase PostgreSQL database
- FastAPI backend with RESTful endpoints

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL (Supabase)
- DBT
- Weather Unlocked API credentials

### Installation
1. Clone the repository:
```bash
git clone https://github.com/maggiebasta/ski-snow-tracker.git
cd ski-snow-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.example` to `.env`
- Update with your credentials:
  - Weather Unlocked API credentials
  - Supabase database URL

4. Initialize database:
```bash
python init_db.py
```

5. Set up DBT:
```bash
cd dbt
dbt deps
dbt seed
dbt run
```

## Usage

### Start the API server:
```bash
uvicorn app.main:app --reload
```

### Fetch snow data:
```bash
curl -X POST http://localhost:8000/api/snow/fetch
```

### Get top snow resorts:
```bash
curl http://localhost:8000/api/snow/top-resorts
```

## Data Sources
- SNOTEL (USDA Natural Resources Conservation Service)
- Weather Unlocked Resort API

## Development
- Uses FastAPI for the backend
- Implements async data fetching
- Includes data validation and error handling
- DBT models for data transformation

## License
Private repository - All rights reserved
