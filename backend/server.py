from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import jwt
import bcrypt
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = "energo_secret_key_2024"
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

app = FastAPI(title="Energo Energy Tracking API")
api_router = APIRouter(prefix="/api")

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    total_consumption: float = 0.0
    current_month_consumption: float = 0.0
    badges: List[str] = []

class EnergyReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime
    consumption_kwh: float
    cost_euros: float
    device_type: str = "general"

class AITip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    potential_savings: str

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked_at: Optional[datetime] = None

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Generate simulated data
def generate_energy_data(user_id: str, days: int = 30):
    """Generate realistic simulated energy consumption data"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_consumption = random.uniform(8, 15)  # Base daily kWh
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        
        # Add realistic variation
        daily_consumption = base_consumption + random.uniform(-3, 4)
        if date.weekday() >= 5:  # Weekend - higher consumption
            daily_consumption *= 1.2
        
        # Seasonal variation
        if date.month in [6, 7, 8]:  # Summer - AC usage
            daily_consumption *= 1.4
        elif date.month in [12, 1, 2]:  # Winter - heating
            daily_consumption *= 1.3
        
        cost = daily_consumption * 0.25  # €0.25 per kWh
        
        reading = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": date,
            "consumption_kwh": round(daily_consumption, 2),
            "cost_euros": round(cost, 2),
            "device_type": "general"
        }
        data.append(reading)
    
    return data

# Authentication endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "total_consumption": 0.0,
        "current_month_consumption": 0.0,
        "badges": []
    }
    
    await db.users.insert_one(user_doc)
    
    # Generate initial energy data
    energy_data = generate_energy_data(user_id, 30)
    await db.energy_readings.insert_many(energy_data)
    
    # Create JWT token
    token = create_jwt_token(user_id)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name
        }
    }

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(user["id"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }

# Energy tracking endpoints
@api_router.get("/dashboard")
async def get_dashboard(user_id: str = Depends(get_current_user)):
    # Get energy readings for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_days_ago}
    }, {"_id": 0}).sort("timestamp", -1).to_list(30)
    
    # Calculate totals
    total_consumption = sum(r["consumption_kwh"] for r in readings)
    total_cost = sum(r["cost_euros"] for r in readings)
    
    # Get this month's data
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_readings = [r for r in readings if r["timestamp"] >= start_of_month]
    month_consumption = sum(r["consumption_kwh"] for r in this_month_readings)
    month_cost = sum(r["cost_euros"] for r in this_month_readings)
    
    # Generate chart data
    daily_data = {}
    for reading in readings:
        date_str = reading["timestamp"].strftime("%Y-%m-%d")
        if date_str not in daily_data:
            daily_data[date_str] = {"consumption": 0, "cost": 0}
        daily_data[date_str]["consumption"] += reading["consumption_kwh"]
        daily_data[date_str]["cost"] += reading["cost_euros"]
    
    chart_data = [
        {
            "date": date,
            "consumption": round(data["consumption"], 2),
            "cost": round(data["cost"], 2)
        }
        for date, data in sorted(daily_data.items())
    ]
    
    return {
        "summary": {
            "total_consumption_kwh": round(total_consumption, 2),
            "total_cost_euros": round(total_cost, 2),
            "month_consumption_kwh": round(month_consumption, 2),
            "month_cost_euros": round(month_cost, 2),
            "average_daily_kwh": round(total_consumption / 30, 2),
            "average_daily_cost": round(total_cost / 30, 2)
        },
        "chart_data": chart_data,
        "recent_readings": readings[:7]
    }

@api_router.get("/ai-tips")
async def get_ai_tips(user_id: str = Depends(get_current_user)):
    tips = [
        {
            "id": str(uuid.uuid4()),
            "title": "Optimize Your Heating",
            "content": "Reduce your thermostat by 1°C to save up to 8% on heating costs. Use programmable timers to heat only when needed.",
            "category": "heating",
            "potential_savings": "€15-25/month"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "LED Light Upgrade",
            "content": "Replace remaining incandescent bulbs with LED lights. They use 75% less energy and last 25 times longer.",
            "category": "lighting",
            "potential_savings": "€5-10/month"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Unplug Standby Devices",
            "content": "Electronics in standby mode can account for 10% of your electricity bill. Use smart power strips to eliminate phantom loads.",
            "category": "electronics",
            "potential_savings": "€8-12/month"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Efficient Appliance Usage",
            "content": "Run dishwashers and washing machines only with full loads. Use cold water when possible - 90% of energy goes to heating water.",
            "category": "appliances",
            "potential_savings": "€12-18/month"
        }
    ]
    
    return {"tips": tips}

@api_router.get("/badges")
async def get_badges(user_id: str = Depends(get_current_user)):
    all_badges = [
        {
            "id": "energy_saver",
            "name": "Energy Saver",
            "description": "Reduced energy consumption by 10% this month",
            "icon": "🌱",
            "unlocked_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "id": "week_warrior",
            "name": "Week Warrior",
            "description": "Stayed under daily target for 7 days straight",
            "icon": "💪",
            "unlocked_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "id": "early_adopter",
            "name": "Early Adopter",
            "description": "Joined Energo community",
            "icon": "🚀",
            "unlocked_at": None
        },
        {
            "id": "efficiency_expert",
            "name": "Efficiency Expert",
            "description": "Achieved 20% energy reduction",
            "icon": "⚡",
            "unlocked_at": None
        }
    ]
    
    return {"badges": all_badges}

@api_router.get("/notifications")
async def get_notifications(user_id: str = Depends(get_current_user)):
    notifications = [
        {
            "id": str(uuid.uuid4()),
            "title": "High Usage Alert",
            "message": "Your energy usage is 15% higher than usual today. Check your heating settings.",
            "type": "alert",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Weekly Summary",
            "message": "Great job! You saved €12 this week compared to last week.",
            "type": "summary",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "read": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "New Badge Earned!",
            "message": "Congratulations! You've unlocked the 'Week Warrior' badge.",
            "type": "achievement",
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "read": True
        }
    ]
    
    return {"notifications": notifications}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()