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
import random
import math
from pathlib import Path
import aiohttp
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

app = FastAPI(title="Energo Smart Energy Management API")
api_router = APIRouter(prefix="/api")

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSettings(BaseModel):
    language: str = "en"  # en, fr, nl
    currency_unit: str = "eur"  # eur, kwh
    notifications_enabled: bool = True
    high_usage_alerts: bool = True
    weekly_summary: bool = True
    subscription_plan: str = "free"  # free, premium
    region: str = "brussels"  # brussels, wallonia, flanders

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    settings: UserSettings = UserSettings()
    total_consumption: float = 0.0
    current_month_consumption: float = 0.0
    badges: List[str] = []
    house_size_m2: float = 150.0  # Default house size for subsidy calculations

class EnergyReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime
    consumption_kwh: float
    cost_euros: float
    device_type: str = "general"
    peak_hour: bool = False
    hourly_breakdown: Optional[List[Dict]] = None

class AIInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    potential_savings: str
    priority: str = "medium"  # low, medium, high
    personalized: bool = True

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str

class ChatHistoryItem(BaseModel):
    id: str
    message: str
    response: str
    timestamp: str
    session_id: str

class SubsidyInfo(BaseModel):
    id: str
    title: str
    description: str
    region: str  # brussels, wallonia, flanders
    amount: str
    eligibility: List[str]
    application_process: str
    deadline: Optional[str] = None
    potential_savings: str
    category: str  # insulation, heating, solar, renovation

# Belgian Energy Subsidies Database
BELGIAN_SUBSIDIES = {
    "brussels": [
        {
            "id": "brussels_insulation",
            "title": "Prime Isolation (Insulation Subsidy)",
            "description": "Financial support for thermal insulation works in Brussels",
            "region": "brussels",
            "amount": "Up to €15/m² for roof insulation, €25/m² for walls",
            "eligibility": [
                "Property in Brussels-Capital Region",
                "Building older than 10 years",
                "Income conditions apply",
                "Professional installer required"
            ],
            "application_process": "Apply online at homegrade.brussels before starting works",
            "deadline": "Ongoing program, budget availability",
            "potential_savings": "€300-1200/year on heating costs",
            "category": "insulation"
        },
        {
            "id": "brussels_solar",
            "title": "Prime Photovoltaïque (Solar Panel Subsidy)",
            "description": "Financial incentive for solar panel installation",
            "region": "brussels",
            "amount": "€350/kWc installed (max 3kWc) = €1,050 total",
            "eligibility": [
                "First-time solar installation",
                "Property in Brussels",
                "Certified installer required",
                "Technical pre-approval needed"
            ],
            "application_process": "Apply at homegrade.brussels with installer quote",
            "deadline": "Subject to annual budget allocation",
            "potential_savings": "€200-500/year in reduced electricity bills",
            "category": "solar"
        },
        {
            "id": "brussels_heating",
            "title": "Prime Chauffage (Heating System Subsidy)",
            "description": "Support for efficient heating system replacement",
            "region": "brussels",
            "amount": "€1000-4000 depending on system type",
            "eligibility": [
                "Replacement of old heating system (>15 years)",
                "High-efficiency equipment required",
                "Property in Brussels",
                "Income-based conditions"
            ],
            "application_process": "Submit application with quotes and technical specifications",
            "deadline": "Apply before installation",
            "potential_savings": "€400-800/year on energy bills",
            "category": "heating"
        }
    ],
    "wallonia": [
        {
            "id": "wallonia_insulation",
            "title": "Prime Habitation (Housing Subsidy)",
            "description": "Comprehensive renovation support including insulation",
            "region": "wallonia",
            "amount": "Up to €20/m² for insulation works",
            "eligibility": [
                "Property in Wallonia region",
                "Building >15 years old",
                "Household income conditions",
                "Minimum R-value requirements"
            ],
            "application_process": "Apply online at energie.wallonie.be",
            "deadline": "Applications accepted year-round",
            "potential_savings": "€500-1500/year on heating costs",
            "category": "insulation"
        },
        {
            "id": "wallonia_heat_pump",
            "title": "Prime Pompe à Chaleur (Heat Pump Subsidy)",
            "description": "Incentive for heat pump installation",
            "region": "wallonia",
            "amount": "€1500-6000 based on performance and income",
            "eligibility": [
                "Replacement of fossil fuel heating",
                "Minimum COP performance requirements",
                "Professional installation mandatory",
                "Property in Wallonia"
            ],
            "application_process": "Pre-approval required, apply with certified installer",
            "deadline": "Ongoing, subject to budget",
            "potential_savings": "€600-1200/year on heating costs",
            "category": "heating"
        }
    ],
    "flanders": [
        {
            "id": "flanders_renovation",
            "title": "Mijn VerbouwPremie (My Renovation Subsidy)",
            "description": "Flemish renovation subsidies for energy improvements",
            "region": "flanders",
            "amount": "€2.5-10/m² for insulation, up to €2500 for heating",
            "eligibility": [
                "Property in Flanders",
                "Building permit may be required",
                "Income conditions for higher amounts",
                "Technical requirements must be met"
            ],
            "application_process": "Apply at mijnverbouwpremie.be before starting works",
            "deadline": "Applications must be submitted before works begin",
            "potential_savings": "€400-1000/year on energy costs",
            "category": "renovation"
        },
        {
            "id": "flanders_solar",
            "title": "Zonnepanelen Subsidie (Solar Panel Subsidy)",
            "description": "Support for residential solar installations",
            "region": "flanders",
            "amount": "Net metering + installation grants up to €1500",
            "eligibility": [
                "Residential property in Flanders",
                "Grid connection available",
                "Certified equipment and installer",
                "Maximum capacity limits apply"
            ],
            "application_process": "Apply through energy supplier and regional authorities",
            "deadline": "Ongoing with periodic policy reviews",
            "potential_savings": "€300-700/year in electricity savings",
            "category": "solar"
        }
    ]
}

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

def generate_realistic_hourly_pattern(base_consumption: float, is_weekend: bool = False, season_factor: float = 1.0) -> List[Dict]:
    """Generate realistic hourly consumption pattern for a single day"""
    hourly_data = []
    
    # Define realistic usage patterns based on typical household behavior
    # Values represent relative consumption multipliers for each hour
    if is_weekend:
        # Weekend pattern - higher morning usage, more distributed throughout day
        hourly_pattern = [
            0.4, 0.3, 0.3, 0.3, 0.4, 0.6,  # 00-05: Night/early morning
            0.8, 1.2, 1.4, 1.6, 1.5, 1.3,  # 06-11: Wake up later, gradual increase
            1.2, 1.0, 1.1, 1.3, 1.4, 1.8,  # 12-17: Home activities, cooking
            2.2, 2.4, 2.0, 1.6, 1.2, 0.8   # 18-23: Evening peak, gradual decrease
        ]
    else:
        # Weekday pattern - clear morning and evening peaks
        hourly_pattern = [
            0.3, 0.2, 0.2, 0.2, 0.3, 0.5,  # 00-05: Night, very low usage
            1.2, 2.0, 2.2, 1.8, 0.8, 0.6,  # 06-11: Morning rush, then away at work
            0.5, 0.4, 0.4, 0.5, 0.6, 1.0,  # 12-17: Low daytime, gradual return
            2.8, 3.2, 2.8, 2.2, 1.4, 0.9   # 18-23: Strong evening peak
        ]
    
    # Apply seasonal adjustments
    if season_factor > 1.1:  # Summer - AC usage during hot hours
        for i in range(12, 20):  # 12 PM - 8 PM
            hourly_pattern[i] *= 1.3
    elif season_factor > 1.05:  # Winter - heating in morning and evening
        for i in range(6, 10):   # Morning heating
            hourly_pattern[i] *= 1.2
        for i in range(17, 23):  # Evening heating
            hourly_pattern[i] *= 1.4
    
    # Generate hourly data
    total_pattern_sum = sum(hourly_pattern)
    
    for hour in range(24):
        # Normalize pattern to match daily total
        hour_consumption = (base_consumption * hourly_pattern[hour] / total_pattern_sum) * 24
        
        # Add some random variation (±15%)
        hour_consumption *= random.uniform(0.85, 1.15)
        
        # Determine if it's a peak hour (top 30% of usage)
        is_peak = hourly_pattern[hour] > 1.5
        
        # Calculate cost (peak vs off-peak rates)
        rate = 0.28 if is_peak else 0.22  # €0.28 peak, €0.22 off-peak
        hour_cost = hour_consumption * rate
        
        hourly_data.append({
            "hour": hour,
            "consumption": round(hour_consumption, 3),
            "cost": round(hour_cost, 3),
            "is_peak": is_peak,
            "rate": rate
        })
    
    return hourly_data

def generate_realistic_energy_data(user_id: str, days: int = 30):
    """Generate highly realistic energy consumption data with proper patterns"""
    data = []
    
    # Base consumption varies by household (10-18 kWh/day typical for Belgian household)
    base_daily_consumption = random.uniform(11, 16)
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        is_weekend = date.weekday() >= 5
        
        # Seasonal factor
        month = date.month
        if month in [6, 7, 8]:  # Summer - AC usage
            season_factor = 1.25
            daily_multiplier = random.uniform(1.1, 1.4)  # Higher variation in summer
        elif month in [12, 1, 2]:  # Winter - heating
            season_factor = 1.35
            daily_multiplier = random.uniform(1.2, 1.5)  # Highest consumption
        else:  # Spring/Fall
            season_factor = 0.95
            daily_multiplier = random.uniform(0.8, 1.1)  # Lower consumption
        
        # Weekend adjustment
        if is_weekend:
            daily_multiplier *= 1.15  # 15% higher on weekends
        
        # Daily weather variation
        weather_factor = random.uniform(0.9, 1.2)
        daily_multiplier *= weather_factor
        
        # Calculate actual daily consumption
        daily_consumption = base_daily_consumption * daily_multiplier * season_factor
        
        # Generate realistic hourly breakdown
        hourly_breakdown = generate_realistic_hourly_pattern(
            daily_consumption, is_weekend, season_factor
        )
        
        # Calculate totals from hourly data
        total_consumption = sum(h["consumption"] for h in hourly_breakdown)
        total_cost = sum(h["cost"] for h in hourly_breakdown)
        
        # Find peak hour
        peak_hour_data = max(hourly_breakdown, key=lambda x: x["consumption"])
        
        reading = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": date,
            "consumption_kwh": round(total_consumption, 2),
            "cost_euros": round(total_cost, 2),
            "device_type": "general",
            "peak_hour": peak_hour_data["is_peak"],
            "hourly_breakdown": hourly_breakdown,
            "is_weekend": is_weekend,
            "season_factor": season_factor
        }
        data.append(reading)
    
    return data

def analyze_consumption_patterns(readings: List[Dict]) -> Dict:
    """Advanced analysis of user's consumption patterns"""
    if not readings:
        return {}
    
    # Basic statistics
    avg_daily = sum(r["consumption_kwh"] for r in readings) / len(readings)
    avg_cost = sum(r["cost_euros"] for r in readings) / len(readings)
    
    # Weekend vs weekday analysis
    weekend_readings = [r for r in readings if r["timestamp"].weekday() >= 5]
    weekday_readings = [r for r in readings if r["timestamp"].weekday() < 5]
    
    weekend_avg = sum(r["consumption_kwh"] for r in weekend_readings) / len(weekend_readings) if weekend_readings else 0
    weekday_avg = sum(r["consumption_kwh"] for r in weekday_readings) / len(weekday_readings) if weekday_readings else 0
    
    # Peak hour analysis
    peak_hours_consumption = 0
    off_peak_consumption = 0
    total_hours = 0
    
    morning_peak = 0  # 6-10 AM
    evening_peak = 0  # 6-10 PM
    daytime_low = 0   # 10 AM - 6 PM
    night_low = 0     # 10 PM - 6 AM
    
    for reading in readings:
        if "hourly_breakdown" in reading and reading["hourly_breakdown"]:
            for hour_data in reading["hourly_breakdown"]:
                hour = hour_data["hour"]
                consumption = hour_data["consumption"]
                total_hours += 1
                
                if hour_data["is_peak"]:
                    peak_hours_consumption += consumption
                else:
                    off_peak_consumption += consumption
                
                # Time period analysis
                if 6 <= hour < 10:
                    morning_peak += consumption
                elif 18 <= hour < 22:
                    evening_peak += consumption
                elif 10 <= hour < 18:
                    daytime_low += consumption
                else:
                    night_low += consumption
    
    # Recent trend analysis
    recent_7 = readings[:7]
    previous_7 = readings[7:14] if len(readings) >= 14 else readings[7:]
    
    recent_avg = sum(r["consumption_kwh"] for r in recent_7) / len(recent_7)
    previous_avg = sum(r["consumption_kwh"] for r in previous_7) / len(previous_7) if previous_7 else recent_avg
    
    trend_change = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
    
    # Cost analysis
    recent_cost_avg = sum(r["cost_euros"] for r in recent_7) / len(recent_7)
    previous_cost_avg = sum(r["cost_euros"] for r in previous_7) / len(previous_7) if previous_7 else recent_cost_avg
    cost_trend = ((recent_cost_avg - previous_cost_avg) / previous_cost_avg * 100) if previous_cost_avg > 0 else 0
    
    # Efficiency metrics
    high_consumption_days = len([r for r in readings if r["consumption_kwh"] > avg_daily * 1.2])
    efficient_days = len([r for r in readings if r["consumption_kwh"] < avg_daily * 0.8])
    
    return {
        "avg_daily_kwh": round(avg_daily, 2),
        "avg_daily_cost": round(avg_cost, 2),
        "weekend_vs_weekday_ratio": round(weekend_avg / weekday_avg, 2) if weekday_avg > 0 else 1,
        "recent_trend_percent": round(trend_change, 1),
        "cost_trend_percent": round(cost_trend, 1),
        "high_consumption_days": high_consumption_days,
        "efficient_days": efficient_days,
        "peak_vs_offpeak_ratio": round(peak_hours_consumption / off_peak_consumption, 2) if off_peak_consumption > 0 else 1,
        "morning_peak_avg": round(morning_peak / len(readings) / 4, 2),  # Avg per hour in morning peak
        "evening_peak_avg": round(evening_peak / len(readings) / 4, 2),  # Avg per hour in evening peak
        "daytime_avg": round(daytime_low / len(readings) / 8, 2),        # Avg per hour during day
        "night_avg": round(night_low / len(readings) / 8, 2),            # Avg per hour at night
        "weekend_avg_kwh": round(weekend_avg, 2),
        "weekday_avg_kwh": round(weekday_avg, 2),
        "total_days_analyzed": len(readings)
    }

def calculate_subsidy_savings(user_patterns: Dict, user_region: str, house_size: float) -> List[Dict]:
    """Calculate personalized subsidy savings based on user's energy profile"""
    subsidies = BELGIAN_SUBSIDIES.get(user_region, [])
    personalized_subsidies = []
    
    avg_annual_cost = user_patterns.get("avg_daily_cost", 3.5) * 365
    avg_daily_kwh = user_patterns.get("avg_daily_kwh", 12)
    
    for subsidy in subsidies:
        personalized_subsidy = subsidy.copy()
        
        # Calculate personalized savings based on category and user data
        if subsidy["category"] == "insulation":
            # Insulation savings: 20-30% of heating costs (assume 60% of total is heating)
            heating_cost = avg_annual_cost * 0.6
            estimated_savings = heating_cost * 0.25  # 25% average savings
            personalized_subsidy["your_annual_savings"] = f"€{int(estimated_savings)}"
            personalized_subsidy["payback_period"] = "3-5 years"
            
            # Calculate subsidy amount based on house size
            if user_region == "wallonia":
                total_subsidy = int(20 * house_size)  # €20/m²
                personalized_subsidy["your_subsidy_amount"] = f"€{total_subsidy}"
            elif user_region == "brussels":
                total_subsidy = int(15 * house_size)  # €15/m² average
                personalized_subsidy["your_subsidy_amount"] = f"€{total_subsidy}"
            elif user_region == "flanders":
                total_subsidy = int(6 * house_size)   # €6/m²
                personalized_subsidy["your_subsidy_amount"] = f"€{total_subsidy}"
            
        elif subsidy["category"] == "solar":
            # Solar savings based on system size and current usage
            annual_kwh = avg_daily_kwh * 365
            system_size_kwp = min(3, annual_kwh / 1000)  # Max 3kWp, or enough to cover usage
            annual_production = system_size_kwp * 1000   # kWh per year in Belgium
            electricity_rate = 0.25
            estimated_savings = min(annual_production * electricity_rate, avg_annual_cost * 0.8)  # Max 80% of bill
            
            personalized_subsidy["your_annual_savings"] = f"€{int(estimated_savings)}"
            personalized_subsidy["payback_period"] = "6-8 years"
            
            if user_region == "brussels":
                subsidy_amount = int(350 * system_size_kwp)  # €350/kWc
                personalized_subsidy["your_subsidy_amount"] = f"€{subsidy_amount}"
            elif user_region == "flanders":
                personalized_subsidy["your_subsidy_amount"] = "€1,500"
            else:  # wallonia
                personalized_subsidy["your_subsidy_amount"] = "€1,200"
            
        elif subsidy["category"] == "heating":
            # Heat pump savings: 30-50% of heating costs
            heating_cost = avg_annual_cost * 0.6
            estimated_savings = heating_cost * 0.4  # 40% average savings
            personalized_subsidy["your_annual_savings"] = f"€{int(estimated_savings)}"
            personalized_subsidy["payback_period"] = "4-6 years"
            personalized_subsidy["your_subsidy_amount"] = "€2,500"
            
        elif subsidy["category"] == "renovation":
            # Comprehensive renovation: 40-60% total energy savings
            estimated_savings = avg_annual_cost * 0.5  # 50% average savings
            personalized_subsidy["your_annual_savings"] = f"€{int(estimated_savings)}"
            personalized_subsidy["payback_period"] = "5-8 years"
            personalized_subsidy["your_subsidy_amount"] = "€5,000"
        
        # Add context-aware recommendations
        personalized_subsidy["personalized_tip"] = generate_subsidy_tip(subsidy, user_patterns)
        
        personalized_subsidies.append(personalized_subsidy)
    
    return personalized_subsidies

def generate_subsidy_tip(subsidy: Dict, patterns: Dict) -> str:
    """Generate personalized tip based on subsidy type and user patterns"""
    category = subsidy["category"]
    evening_high = patterns.get("evening_peak_avg", 0) > patterns.get("daytime_avg", 0) * 1.5
    weekend_high = patterns.get("weekend_vs_weekday_ratio", 1) > 1.2
    
    if category == "insulation":
        if weekend_high:
            return "Your weekend usage is high, suggesting you're home more. Insulation will provide constant comfort and savings."
        return "With your heating patterns, insulation could significantly reduce your energy bills."
    
    elif category == "solar":
        avg_daily = patterns.get("avg_daily_kwh", 12)
        if avg_daily > 15:
            return f"Your high daily usage ({avg_daily:.1f} kWh) makes solar panels an excellent investment."
        return "Solar panels can cover a significant portion of your electricity needs and reduce your bills."
    
    elif category == "heating":
        if evening_high:
            return "Your evening consumption peaks suggest heating usage. A heat pump could provide the same comfort for less."
        return "Modern heating systems can maintain comfort while using 60% less energy."
    
    return "This subsidy aligns well with your energy usage patterns."

def generate_personalized_insights(user_patterns: Dict, user_id: str) -> List[Dict]:
    """Generate highly personalized AI insights based on detailed consumption patterns"""
    insights = []
    
    if not user_patterns:
        return [{
            "id": str(uuid.uuid4()),
            "title": "Welcome to Smart Energy Management",
            "content": "Start tracking your energy usage to get personalized insights and savings recommendations.",
            "category": "welcome",
            "potential_savings": "Up to €20/month",
            "priority": "high",
            "personalized": False
        }]
    
    # Evening peak analysis
    evening_peak = user_patterns.get("evening_peak_avg", 0)
    daytime_avg = user_patterns.get("daytime_avg", 0)
    if evening_peak > daytime_avg * 1.3:  # Evening is 30% higher than daytime
        peak_percentage = int(((evening_peak - daytime_avg) / daytime_avg) * 100)
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Evening Energy Peak Detected",
            "content": f"Your evening consumption (7-10 PM) is {peak_percentage}% higher than your daily average. Consider lowering lighting usage, using LED bulbs, or shifting some activities to off-peak hours.",
            "category": "timing",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.15, 1)}/day",
            "priority": "high",
            "personalized": True
        })
    
    # Weekend usage patterns
    weekend_ratio = user_patterns.get("weekend_vs_weekday_ratio", 1)
    if weekend_ratio > 1.2:
        weekend_increase = int((weekend_ratio - 1) * 100)
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Weekend Energy Spike",
            "content": f"You use {weekend_increase}% more energy on weekends. This is normal for home activities, but you can save by unplugging devices on standby and optimizing heating/cooling schedules.",
            "category": "weekend",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.12, 1)}/weekend",
            "priority": "medium",
            "personalized": True
        })
    
    # Recent trend analysis
    trend = user_patterns.get("recent_trend_percent", 0)
    cost_trend = user_patterns.get("cost_trend_percent", 0)
    if trend < -5:  # Significant improvement
        saved_amount = abs(cost_trend * user_patterns['avg_daily_cost'] / 100) * 7  # Weekly savings
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Great Energy Savings!",
            "content": f"Excellent! You reduced your energy usage by {abs(trend):.1f}% this week. You saved approximately €{saved_amount:.1f} compared to last week. Keep up the great work!",
            "category": "achievement",
            "potential_savings": f"€{saved_amount:.1f}/week saved",
            "priority": "low",
            "personalized": True
        })
    elif trend > 10:  # Concerning increase
        extra_cost = (trend * user_patterns['avg_daily_cost'] / 100) * 7  # Weekly extra cost
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Rising Energy Usage Alert",
            "content": f"Your energy usage increased by {trend:.1f}% this week, costing an extra €{extra_cost:.1f}. Check if any new appliances are running or if heating/cooling settings changed.",
            "category": "alert",
            "potential_savings": f"€{extra_cost:.1f}/week potential savings",
            "priority": "high",
            "personalized": True
        })
    
    # Peak vs off-peak optimization
    peak_ratio = user_patterns.get("peak_vs_offpeak_ratio", 1)
    if peak_ratio > 1.5:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Peak Hour Optimization Opportunity",
            "content": f"You use significantly more energy during expensive peak hours. Try shifting dishwasher, washing machine, and charging activities to off-peak times (10 PM - 6 AM) for lower rates.",
            "category": "optimization",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.18, 1)}/day",
            "priority": "medium",
            "personalized": True
        })
    
    # Efficiency recognition
    efficient_days = user_patterns.get("efficient_days", 0)
    total_days = user_patterns.get("total_days_analyzed", 30)
    if efficient_days > total_days * 0.4:  # More than 40% efficient days
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Energy Efficiency Champion",
            "content": f"Outstanding! You had {efficient_days} energy-efficient days out of {total_days}. You're well on your way to earning advanced efficiency badges and maximizing your savings.",
            "category": "gamification",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.25, 1)}/month in potential savings",
            "priority": "low",
            "personalized": True
        })
    
    return insights

# Authentication endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "settings": UserSettings().dict(),
        "total_consumption": 0.0,
        "current_month_consumption": 0.0,
        "badges": [],
        "house_size_m2": 150.0  # Default house size
    }
    
    await db.users.insert_one(user_doc)
    
    # Generate realistic energy data
    energy_data = generate_realistic_energy_data(user_id, 30)
    await db.energy_readings.insert_many(energy_data)
    
    token = create_jwt_token(user_id)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "settings": UserSettings().dict()
        }
    }

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "settings": user.get("settings", UserSettings().dict())
        }
    }

# Logout endpoint
@api_router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    """Logout endpoint - client should remove token locally"""
    return {"message": "Logged out successfully"}

# Enhanced Dashboard endpoint with realistic data
@api_router.get("/dashboard")
async def get_dashboard(period: str = "week", user_id: str = Depends(get_current_user)):
    # Determine date range based on period
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
        comparison_start = now - timedelta(days=2)
        comparison_end = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(days=7)
        comparison_start = now - timedelta(days=14)
        comparison_end = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
        comparison_start = now - timedelta(days=60)
        comparison_end = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)  # Default to week
        comparison_start = now - timedelta(days=14)
        comparison_end = now - timedelta(days=7)
    
    # Get current period data
    current_readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": start_date}
    }, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    
    # Get comparison period data
    comparison_readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": comparison_start, "$lt": comparison_end}
    }, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    
    # Calculate current period totals
    current_consumption = sum(r["consumption_kwh"] for r in current_readings)
    current_cost = sum(r["cost_euros"] for r in current_readings)
    
    # Calculate comparison period totals
    comparison_consumption = sum(r["consumption_kwh"] for r in comparison_readings)
    comparison_cost = sum(r["cost_euros"] for r in comparison_readings)
    
    # Calculate changes
    consumption_change = ((current_consumption - comparison_consumption) / comparison_consumption * 100) if comparison_consumption > 0 else 0
    cost_change = ((current_cost - comparison_cost) / comparison_cost * 100) if comparison_cost > 0 else 0
    
    # Generate enhanced chart data with realistic patterns
    if period == "day":
        # Hourly data for day view - show realistic daily pattern
        if current_readings and "hourly_breakdown" in current_readings[0]:
            hourly_breakdown = current_readings[0]["hourly_breakdown"]
            chart_data = [
                {
                    "label": f"{hour_data['hour']:02d}:00",
                    "value": round(hour_data["consumption"], 2),
                    "cost": round(hour_data["cost"], 2),
                    "color": "#FF5722" if hour_data["is_peak"] else "#4CAF50"
                }
                for hour_data in hourly_breakdown
            ]
        else:
            chart_data = []
    else:
        # Daily data for week/month view
        daily_data = {}
        for reading in current_readings:
            date_str = reading["timestamp"].strftime("%Y-%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = {"consumption": 0, "cost": 0, "is_weekend": reading["timestamp"].weekday() >= 5}
            daily_data[date_str]["consumption"] += reading["consumption_kwh"]
            daily_data[date_str]["cost"] += reading["cost_euros"]
        
        avg_consumption = current_consumption / len(daily_data) if daily_data else 0
        
        chart_data = [
            {
                "label": datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d"),
                "value": round(data["consumption"], 2),
                "cost": round(data["cost"], 2),
                "color": "#FF9800" if data["is_weekend"] else ("#FF5722" if data["consumption"] > avg_consumption else "#4CAF50")
            }
            for date, data in sorted(daily_data.items())
        ]
    
    # Generate insights with realistic data
    patterns = analyze_consumption_patterns(current_readings)
    
    # Create personalized insight card message
    if consumption_change > 10:
        insight_message = f"Your energy usage increased by {consumption_change:.0f}% compared to last {period}. Check your heating/cooling settings."
        insight_type = "warning"
    elif consumption_change < -5:
        saved_amount = abs(cost_change * current_cost / 100)
        insight_message = f"Great job! You saved €{saved_amount:.1f} compared to last {period}. Keep up the excellent work!"
        insight_type = "success"
    else:
        insight_message = f"Your energy usage is stable compared to last {period}. Consider optimization opportunities."
        insight_type = "info"
    
    # Weekly goal progress (realistic based on patterns)
    target_reduction = 0.1  # 10% reduction goal
    weekly_goal_kwh = patterns.get("avg_daily_kwh", 15) * 7 * (1 - target_reduction)
    current_week_consumption = current_consumption if period == "week" else current_consumption * 7 / max(len(set(r["timestamp"].date() for r in current_readings)), 1)
    
    if weekly_goal_kwh > 0:
        goal_progress = max(0, min(100, ((weekly_goal_kwh - current_week_consumption + weekly_goal_kwh * target_reduction) / (weekly_goal_kwh * target_reduction)) * 100))
    else:
        goal_progress = 50
    
    return {
        "summary": {
            "current_consumption_kwh": round(current_consumption, 2),
            "current_cost_euros": round(current_cost, 2),
            "consumption_change_percent": round(consumption_change, 1),
            "cost_change_percent": round(cost_change, 1),
            "average_daily_kwh": round(current_consumption / max(len(set(r["timestamp"].date() for r in current_readings)), 1), 2),
            "average_daily_cost": round(current_cost / max(len(set(r["timestamp"].date() for r in current_readings)), 1), 2),
            "period": period
        },
        "insight_card": {
            "message": insight_message,
            "type": insight_type,
            "savings_amount": round(abs(cost_change * current_cost / 100), 1) if cost_change < 0 else 0
        },
        "progress": {
            "weekly_goal_percent": round(goal_progress, 1),
            "goal_description": f"Weekly energy reduction goal: {goal_progress:.0f}% achieved",
            "estimated_savings": f"€{round(patterns.get('avg_daily_cost', 3) * 7 * target_reduction, 1)}/week potential"
        },
        "chart_data": chart_data,
        "patterns": patterns
    }

# Enhanced AI Assistant endpoint with realistic insights
@api_router.get("/ai-insights")
async def get_ai_insights(user_id: str = Depends(get_current_user)):
    # Get user data including settings
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_region = user.get("settings", {}).get("region", "brussels")
    house_size = user.get("house_size_m2", 150.0)
    
    # Get user's recent consumption data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_days_ago}
    }, {"_id": 0}).sort("timestamp", -1).to_list(100)
    
    # Analyze patterns with enhanced analysis
    patterns = analyze_consumption_patterns(readings)
    
    # Generate personalized insights
    insights = generate_personalized_insights(patterns, user_id)
    
    # Get personalized subsidies
    subsidies = calculate_subsidy_savings(patterns, user_region, house_size)
    
    return {
        "insights": insights, 
        "patterns": patterns,
        "subsidies": subsidies,
        "region": user_region
    }

# Gamification - Enhanced badges with progress tracking
@api_router.get("/badges")
async def get_badges(user_id: str = Depends(get_current_user)):
    # Get user's energy data for badge calculations
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_days_ago}
    }, {"_id": 0}).to_list(100)
    
    patterns = analyze_consumption_patterns(readings)
    
    # Calculate badge unlocks based on actual performance
    all_badges = [
        {
            "id": "early_adopter",
            "name": "Early Adopter",
            "description": "Joined Energo Smart community",
            "icon": "🚀",
            "category": "milestone",
            "unlocked_at": datetime.utcnow() - timedelta(days=1),
            "progress": 100,
            "reward_euros": 0
        },
        {
            "id": "energy_saver",
            "name": "Energy Saver",
            "description": "Reduced energy consumption by 10% this month",
            "icon": "🌱",
            "category": "efficiency",
            "unlocked_at": datetime.utcnow() - timedelta(days=5) if patterns.get("recent_trend_percent", 0) < -8 else None,
            "progress": max(0, min(100, abs(patterns.get("recent_trend_percent", 0)) * 10)) if patterns.get("recent_trend_percent", 0) < 0 else 0,
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 30 * 0.1, 0) if patterns.get("recent_trend_percent", 0) < -8 else 0
        },
        {
            "id": "peak_optimizer",
            "name": "Peak Hour Optimizer",
            "description": "Reduced peak hour usage efficiently",
            "icon": "⚡",
            "category": "optimization",
            "unlocked_at": datetime.utcnow() - timedelta(days=3) if patterns.get("peak_vs_offpeak_ratio", 2) < 1.3 else None,
            "progress": max(0, min(100, (2 - patterns.get("peak_vs_offpeak_ratio", 2)) * 50)),
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 30 * 0.15, 0) if patterns.get("peak_vs_offpeak_ratio", 2) < 1.3 else 0
        },
        {
            "id": "weekend_warrior",
            "name": "Weekend Warrior",
            "description": "Maintained efficient weekend usage",
            "icon": "💪",
            "category": "consistency",
            "unlocked_at": datetime.utcnow() - timedelta(days=2) if patterns.get("weekend_vs_weekday_ratio", 1.5) < 1.15 else None,
            "progress": max(0, min(100, (1.5 - patterns.get("weekend_vs_weekday_ratio", 1.5)) * 100)),
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 8 * 0.12, 0) if patterns.get("weekend_vs_weekday_ratio", 1.5) < 1.15 else 0
        },
        {
            "id": "subsidy_explorer",
            "name": "Subsidy Explorer",
            "description": "Explored available energy subsidies",
            "icon": "💰",
            "category": "savings",
            "unlocked_at": datetime.utcnow() - timedelta(hours=1),
            "progress": 100,
            "reward_euros": 0
        },
        {
            "id": "efficiency_expert",
            "name": "Efficiency Expert",
            "description": "Achieved 20% energy reduction",
            "icon": "🏆",
            "category": "efficiency",
            "unlocked_at": None,
            "progress": max(0, min(100, abs(patterns.get("recent_trend_percent", 0)) * 5)) if patterns.get("recent_trend_percent", 0) < 0 else 0,
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 30 * 0.2, 0)
        }
    ]
    
    return {"badges": all_badges}

# Challenges endpoint
@api_router.get("/challenges")
async def get_challenges(user_id: str = Depends(get_current_user)):
    # Get user patterns for realistic challenge progress
    week_start = datetime.utcnow() - timedelta(days=7)
    recent_readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": week_start}
    }, {"_id": 0}).to_list(100)
    
    patterns = analyze_consumption_patterns(recent_readings)
    
    challenges = [
        {
            "id": "reduce_evening_usage",
            "title": "Evening Energy Challenge",
            "description": "Reduce evening usage (7-10 PM) by 15% this week",
            "target_value": 15.0,  # percentage reduction
            "current_progress": max(0, min(15, abs(patterns.get("recent_trend_percent", 0)) * 1.5)) if patterns.get("recent_trend_percent", 0) < 0 else random.uniform(2, 8),
            "deadline": datetime.utcnow() + timedelta(days=4),
            "reward_badge": "evening_optimizer",
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 7 * 0.15, 1),
            "active": True
        },
        {
            "id": "weekend_efficiency",
            "title": "Weekend Efficiency Master",
            "description": "Keep weekend usage below 115% of weekday average",
            "target_value": 115.0,  # percentage of weekday usage
            "current_progress": max(100, min(115, patterns.get("weekend_vs_weekday_ratio", 1.2) * 100)),
            "deadline": datetime.utcnow() + timedelta(days=2),
            "reward_badge": "weekend_master",
            "reward_euros": round(patterns.get("avg_daily_cost", 3) * 2 * 0.12, 1),
            "active": True
        },
        {
            "id": "monthly_saver",
            "title": "Monthly Energy Saver",
            "description": "Save €25 compared to last month",
            "target_value": 25.0,  # euros
            "current_progress": max(0, min(25, abs(patterns.get("cost_trend_percent", 0)) * patterns.get("avg_daily_cost", 3) * 0.3)) if patterns.get("cost_trend_percent", 0) < 0 else random.uniform(3, 12),
            "deadline": datetime.utcnow() + timedelta(days=12),
            "reward_badge": "monthly_champion",
            "reward_euros": 25,
            "active": True
        }
    ]
    
    return {"challenges": challenges}

# Settings endpoints
@api_router.get("/settings")
async def get_settings(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = user.get("settings", UserSettings().dict())
    
    # Temporarily set premium access for testing
    settings["subscription_plan"] = "premium"
    
    # Update user in database with premium access
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"settings": settings}}
    )
    
    return {"settings": settings}

@api_router.put("/settings")
async def update_settings(settings: UserSettings, user_id: str = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"settings": settings.dict()}}
    )
    return {"message": "Settings updated successfully", "settings": settings.dict()}

# Subscription endpoint
@api_router.get("/subscription")
async def get_subscription_info(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    settings = user.get("settings", {})
    
    # Force premium for testing
    current_plan = "premium"
    
    # Update user settings with premium
    if settings.get("subscription_plan") != "premium":
        settings["subscription_plan"] = "premium"
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"settings": settings}}
        )
    
    plans = {
        "free": {
            "name": "Free Plan",
            "price": 0,
            "features": [
                "Basic energy tracking",
                "Weekly summaries",
                "3 AI insights per week",
                "Basic badges",
                "Regional subsidies overview"
            ],
            "limitations": [
                "Limited historical data (30 days)",
                "Basic insights only",
                "No interactive AI chat"
            ]
        },
        "premium": {
            "name": "Premium Plan",
            "price": 8,
            "features": [
                "Advanced energy analytics",
                "Unlimited AI insights",
                "Interactive AI chat assistant",
                "Real-time subsidy updates",
                "Personalized subsidy calculator",
                "Predictive forecasting",
                "Custom challenges",
                "All badges & achievements",
                "Export data",
                "Priority support"
            ],
            "limitations": []
        }
    }
    
    return {
        "current_plan": current_plan,
        "plans": plans,
        "stripe_integration": "placeholder"
    }

# Notifications endpoint
@api_router.get("/notifications")
async def get_notifications(user_id: str = Depends(get_current_user)):
    notifications = [
        {
            "id": str(uuid.uuid4()),
            "title": "Energy Saver Badge Earned!",
            "message": "Congratulations! You've earned the Energy Saver badge for reducing usage by 10% this week. You saved €15!",
            "type": "achievement",
            "timestamp": datetime.utcnow() - timedelta(hours=1),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Evening Peak Alert",
            "message": "Your evening usage (7-10 PM) is 28% higher than average. Consider shifting some activities to save €8/week.",
            "type": "insight",
            "timestamp": datetime.utcnow() - timedelta(hours=3),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "title": "New Subsidy Available!",
            "message": "A new insulation subsidy is available in your region. Potential savings: €800/year. Check AI Assistant for details.",
            "type": "subsidy",
            "timestamp": datetime.utcnow() - timedelta(hours=6),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Weekly Goal Achievement",
            "message": "Amazing! You're 85% toward your weekly energy reduction goal. Keep it up to earn the Weekly Champion badge!",
            "type": "progress",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "read": True
        }
    ]
    
    return {"notifications": notifications}

# Interactive AI Chat endpoint
@api_router.post("/ai-chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage, user_id: str = Depends(get_current_user)):
    """Interactive AI chat for energy advice and questions."""
    try:
        # Get user data for personalization
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        settings = user.get("settings", {})
        subscription_plan = settings.get("subscription_plan", "free")
        
        # Generate or use existing session ID
        session_id = chat_message.session_id or str(uuid.uuid4())
        
        # Get user's recent energy data for context
        recent_readings = list(await db.energy_readings.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(5).to_list(length=5))
        
        # Create context for AI
        context = f"""
        You are an expert energy advisor for Belgian residents. The user has a {subscription_plan} subscription.
        
        User Profile:
        - Name: {user.get('name', 'User')}
        - Region: {settings.get('region', 'Brussels')}
        - Language: {settings.get('language', 'en')}
        - Subscription: {subscription_plan}
        
        Recent Energy Data:
        """
        
        if recent_readings:
            for reading in recent_readings:
                context += f"- {reading.get('timestamp', 'N/A')}: {reading.get('consumption_kwh', 0)} kWh, €{reading.get('cost_euros', 0)}\n"
        else:
            context += "- No recent energy data available\n"
            
        context += """
        
        Instructions:
        1. Provide personalized energy advice based on the user's data and region
        2. If asked about subsidies, provide specific information for their region (Brussels/Flanders/Wallonia)
        3. Always be helpful, accurate, and encouraging
        4. For premium users, provide more detailed analysis and predictions
        5. For free users, mention premium features when relevant but still provide valuable basic advice
        6. Keep responses concise but informative
        7. Use euros (€) for all financial references
        """
        
        # Initialize AI chat
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        if not emergent_key:
            raise HTTPException(status_code=500, detail="AI service unavailable")
            
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=context
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=chat_message.message)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)
        
        # For premium users, add real-time Fluvius data if the query seems to need current data
        if subscription_plan == "premium" and any(keyword in chat_message.message.lower() for keyword in ['energy', 'consumption', 'data', 'current', 'latest', 'new', 'update']):
            try:
                fluvius_data = await get_fluvius_data(settings.get('region', 'Brussels'))
                if fluvius_data and fluvius_data.get('data'):
                    data_summary = f"📊 **Real-time Energy Data from {fluvius_data['data_source']}:**\n"
                    for item in fluvius_data['data'][:3]:  # Show top 3 results
                        data_summary += f"• {item.get('municipality', 'N/A')}: {item.get('consumption_kwh', item.get('consumption_mwh', 0))} {'kWh' if 'consumption_kwh' in item else 'MWh'} ({item.get('period', 'N/A')})\n"
                    ai_response += f"\n\n{data_summary}"
            except Exception as e:
                logger.warning(f"Fluvius data fetch failed: {e}")
        
        # Store chat history
        chat_history = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "message": chat_message.message,
            "response": ai_response,
            "timestamp": datetime.utcnow(),
            "subscription_plan": subscription_plan
        }
        
        await db.chat_history.insert_one(chat_history)
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail="AI chat service unavailable")

async def search_real_time_info(query: str, region: str) -> str:
    """Search for real-time energy subsidy information."""
    try:
        search_urls = {
            "brussels": [
                "https://www.brusselstimes.com/energy",
                "https://www.brussels.be/subsidies"
            ],
            "flanders": [
                "https://www.vlaanderen.be/wonen-en-energie",
                "https://www.energiesparen.be"
            ],
            "wallonia": [
                "https://energie.wallonie.be",
                "https://www.spw.wallonie.be"
            ]
        }
        
        urls = search_urls.get(region.lower(), search_urls["brussels"])
        
        # Simple web search simulation for demo
        # In production, you would implement proper web scraping here
        mock_results = [
            f"🔍 Recent energy news for {region}:",
            "• New insulation subsidies available - up to €3,000",
            "• Heat pump incentives increased by 15%", 
            "• Solar panel premiums extended until 2025",
            "• Energy efficiency audits now 50% subsidized"
        ]
        
        return "\n".join(mock_results)
        
    except Exception as e:
        logger.error(f"Real-time search error: {e}")
        return ""

async def get_fluvius_data(user_location: str = "Brussels") -> Dict:
    """
    Integrate with Fluvius Open Data API for realistic energy consumption data.
    Fallback to mock data if API is unavailable or user is outside Belgium.
    """
    try:
        # Fluvius Open Data API endpoint
        fluvius_api_url = "https://opendata.fluvius.be/api/explore/v2.1/catalog/datasets/consumption-electricity-municipality/records"
        
        async with aiohttp.ClientSession() as session:
            params = {
                "limit": 10,
                "where": f"municipality like '{user_location}%'",
                "order_by": "period desc"
            }
            
            async with session.get(fluvius_api_url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('results'):
                        # Process Fluvius data
                        fluvius_results = []
                        for record in data['results'][:5]:
                            fields = record.get('record', {}).get('fields', {})
                            fluvius_results.append({
                                'municipality': fields.get('municipality', user_location),
                                'period': fields.get('period', '2024'),
                                'consumption_mwh': fields.get('consumption_mwh', 0),
                                'connections': fields.get('connections', 0),
                                'source': 'Fluvius Open Data'
                            })
                        
                        return {
                            'data_source': 'Fluvius Open Data API',
                            'location': user_location,
                            'data': fluvius_results,
                            'is_real_data': True
                        }
                
        # If no data from Fluvius, return mock data
        raise Exception("No Fluvius data available")
        
    except Exception as e:
        logger.warning(f"Fluvius API unavailable: {e}. Using mock data.")
        
        # Generate realistic mock data
        mock_data = []
        base_consumption = random.uniform(3500, 4500)  # Annual kWh for average household
        
        for i in range(5):
            month_factor = 1 + (0.3 * math.sin(2 * math.pi * i / 12))  # Seasonal variation
            daily_consumption = (base_consumption / 365) * month_factor
            
            mock_data.append({
                'municipality': user_location,
                'period': f'2024-{12-i:02d}',
                'consumption_kwh': round(daily_consumption * 30, 2),  # Monthly consumption
                'connections': random.randint(45000, 55000),
                'source': 'Simulated Data'
            })
        
        return {
            'data_source': 'Mock Data (Fluvius API unavailable)',
            'location': user_location,
            'data': mock_data,
            'is_real_data': False
        }

# Get chat history endpoint
@api_router.get("/ai-chat/history")
async def get_chat_history(session_id: Optional[str] = None, user_id: str = Depends(get_current_user)):
    """Get chat history for a user or specific session."""
    try:
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id
            
        chat_history = list(await db.chat_history.find(
            query
        ).sort("timestamp", -1).limit(50).to_list(length=50))
        
        return {"chat_history": chat_history}
        
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()