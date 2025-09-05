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

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    settings: UserSettings = UserSettings()
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
    peak_hour: bool = False

class AIInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str
    potential_savings: str
    priority: str = "medium"  # low, medium, high
    personalized: bool = True

class Challenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    target_value: float
    current_progress: float
    deadline: datetime
    reward_badge: str
    active: bool = True

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked_at: Optional[datetime] = None
    category: str = "energy_saving"

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

def generate_realistic_energy_data(user_id: str, days: int = 30):
    """Generate highly realistic simulated energy consumption data"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_consumption = random.uniform(10, 18)  # Base daily kWh for household
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=i)
        
        # Daily pattern variations
        daily_multiplier = 1.0
        
        # Weekend usage (typically higher)
        if date.weekday() >= 5:
            daily_multiplier *= 1.15
        
        # Seasonal variations
        month = date.month
        if month in [6, 7, 8]:  # Summer - AC usage
            daily_multiplier *= 1.35
        elif month in [12, 1, 2]:  # Winter - heating
            daily_multiplier *= 1.25
        elif month in [3, 4, 5, 9, 10, 11]:  # Spring/Fall
            daily_multiplier *= 0.9
        
        # Weather-like randomness (some days higher/lower)
        weather_factor = random.uniform(0.85, 1.20)
        daily_multiplier *= weather_factor
        
        # Calculate hourly consumption for the day
        daily_total = base_consumption * daily_multiplier
        
        # Distribute across peak and off-peak hours
        peak_hours = [7, 8, 9, 17, 18, 19, 20, 21]  # Morning and evening peaks
        peak_consumption = daily_total * 0.6  # 60% during peak hours
        off_peak_consumption = daily_total * 0.4  # 40% during off-peak
        
        # Add some hourly variation throughout the day
        hourly_variations = []
        for hour in range(24):
            if hour in peak_hours:
                hour_consumption = (peak_consumption / len(peak_hours)) * random.uniform(0.8, 1.4)
                is_peak = True
            else:
                hour_consumption = (off_peak_consumption / (24 - len(peak_hours))) * random.uniform(0.6, 1.2)
                is_peak = False
            
            hourly_variations.append({
                "hour": hour,
                "consumption": hour_consumption,
                "is_peak": is_peak
            })
        
        # Cost calculation (peak vs off-peak rates)
        peak_rate = 0.28  # €0.28 per kWh during peak
        off_peak_rate = 0.22  # €0.22 per kWh during off-peak
        
        total_cost = 0
        for hour_data in hourly_variations:
            rate = peak_rate if hour_data["is_peak"] else off_peak_rate
            total_cost += hour_data["consumption"] * rate
        
        reading = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": date,
            "consumption_kwh": round(daily_total, 2),
            "cost_euros": round(total_cost, 2),
            "device_type": "general",
            "peak_hour": max(hourly_variations, key=lambda x: x["consumption"])["is_peak"],
            "hourly_breakdown": hourly_variations
        }
        data.append(reading)
    
    return data

def analyze_consumption_patterns(readings: List[Dict]) -> Dict:
    """Analyze user's consumption patterns for personalized insights"""
    if not readings:
        return {}
    
    # Calculate averages
    avg_daily = sum(r["consumption_kwh"] for r in readings) / len(readings)
    avg_cost = sum(r["cost_euros"] for r in readings) / len(readings)
    
    # Find peak usage days
    peak_days = sorted(readings, key=lambda x: x["consumption_kwh"], reverse=True)[:3]
    
    # Weekend vs weekday analysis
    weekend_readings = [r for r in readings if r["timestamp"].weekday() >= 5]
    weekday_readings = [r for r in readings if r["timestamp"].weekday() < 5]
    
    weekend_avg = sum(r["consumption_kwh"] for r in weekend_readings) / len(weekend_readings) if weekend_readings else 0
    weekday_avg = sum(r["consumption_kwh"] for r in weekday_readings) / len(weekday_readings) if weekday_readings else 0
    
    # Recent trend (last 7 days vs previous 7 days)
    recent_7 = readings[:7]
    previous_7 = readings[7:14] if len(readings) >= 14 else readings[7:]
    
    recent_avg = sum(r["consumption_kwh"] for r in recent_7) / len(recent_7)
    previous_avg = sum(r["consumption_kwh"] for r in previous_7) / len(previous_7) if previous_7 else recent_avg
    
    trend_change = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
    
    return {
        "avg_daily_kwh": round(avg_daily, 2),
        "avg_daily_cost": round(avg_cost, 2),
        "peak_usage_day": peak_days[0] if peak_days else None,
        "weekend_vs_weekday_ratio": round(weekend_avg / weekday_avg, 2) if weekday_avg > 0 else 1,
        "recent_trend_percent": round(trend_change, 1),
        "high_consumption_days": len([r for r in readings if r["consumption_kwh"] > avg_daily * 1.2]),
        "efficient_days": len([r for r in readings if r["consumption_kwh"] < avg_daily * 0.8])
    }

def generate_personalized_insights(user_patterns: Dict, user_id: str) -> List[Dict]:
    """Generate personalized AI insights based on user's consumption patterns"""
    insights = []
    
    if not user_patterns:
        # Default insights for new users
        return [
            {
                "id": str(uuid.uuid4()),
                "title": "Welcome to Smart Energy Management",
                "content": "Start tracking your energy usage to get personalized insights and savings recommendations.",
                "category": "welcome",
                "potential_savings": "Up to €20/month",
                "priority": "high",
                "personalized": False
            }
        ]
    
    # Trend-based insights
    if user_patterns.get("recent_trend_percent", 0) > 10:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Rising Energy Usage Alert",
            "content": f"Your energy usage increased by {user_patterns['recent_trend_percent']}% this week. Check if any new appliances are running or heating/cooling settings changed.",
            "category": "alert",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.15, 1)}/day",
            "priority": "high",
            "personalized": True
        })
    elif user_patterns.get("recent_trend_percent", 0) < -5:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Great Energy Savings!",
            "content": f"Excellent! You reduced your energy usage by {abs(user_patterns['recent_trend_percent'])}% this week. Keep up the great work!",
            "category": "achievement",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.05, 1)}/day saved",
            "priority": "medium",
            "personalized": True
        })
    
    # Weekend usage insights
    if user_patterns.get("weekend_vs_weekday_ratio", 1) > 1.2:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Weekend Energy Spike",
            "content": f"You use {round((user_patterns['weekend_vs_weekday_ratio'] - 1) * 100)}% more energy on weekends. Try unplugging standby devices and optimizing heating/cooling schedules.",
            "category": "optimization",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.1, 1)}/weekend",
            "priority": "medium",
            "personalized": True
        })
    
    # Peak usage insights
    if user_patterns.get("high_consumption_days", 0) > 5:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Optimize Peak Usage",
            "content": f"You had {user_patterns['high_consumption_days']} high-usage days this month. Peak usage often occurs at 7-9 AM and 6-9 PM. Shift some activities to off-peak hours.",
            "category": "timing",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.12, 1)}/day",
            "priority": "medium",
            "personalized": True
        })
    
    # Efficiency praise
    if user_patterns.get("efficient_days", 0) > 10:
        insights.append({
            "id": str(uuid.uuid4()),
            "title": "Energy Efficiency Champion",
            "content": f"Amazing! You had {user_patterns['efficient_days']} energy-efficient days this month. You're on track to earn the 'Green Champion' badge!",
            "category": "gamification",
            "potential_savings": f"€{round(user_patterns['avg_daily_cost'] * 0.2, 1)}/month in savings",
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
        "badges": []
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

# Enhanced Dashboard endpoint
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
    
    # Generate chart data
    if period == "day":
        # Hourly data for day view
        hourly_data = {}
        for reading in current_readings:
            if "hourly_breakdown" in reading:
                for hour_data in reading["hourly_breakdown"]:
                    hour = hour_data["hour"]
                    if hour not in hourly_data:
                        hourly_data[hour] = {"consumption": 0, "cost": 0}
                    rate = 0.28 if hour_data["is_peak"] else 0.22
                    hourly_data[hour]["consumption"] += hour_data["consumption"]
                    hourly_data[hour]["cost"] += hour_data["consumption"] * rate
        
        chart_data = [
            {
                "label": f"{hour:02d}:00",
                "value": round(data["consumption"], 2),
                "cost": round(data["cost"], 2),
                "color": "#4CAF50" if data["consumption"] < current_consumption / 24 else "#FF5722"
            }
            for hour, data in sorted(hourly_data.items())
        ]
    else:
        # Daily data for week/month view
        daily_data = {}
        for reading in current_readings:
            date_str = reading["timestamp"].strftime("%Y-%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = {"consumption": 0, "cost": 0}
            daily_data[date_str]["consumption"] += reading["consumption_kwh"]
            daily_data[date_str]["cost"] += reading["cost_euros"]
        
        avg_consumption = current_consumption / len(daily_data) if daily_data else 0
        
        chart_data = [
            {
                "label": datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d"),
                "value": round(data["consumption"], 2),
                "cost": round(data["cost"], 2),
                "color": "#4CAF50" if data["consumption"] < avg_consumption else "#FF5722"
            }
            for date, data in sorted(daily_data.items())
        ]
    
    # Generate insights
    patterns = analyze_consumption_patterns(current_readings)
    
    # Create insight card message
    if consumption_change > 10:
        insight_message = f"Today you used {consumption_change:.0f}% more energy than yesterday."
        insight_type = "warning"
    elif consumption_change < -5:
        saved_amount = abs(cost_change * current_cost / 100)
        insight_message = f"Great job! You saved €{saved_amount:.1f} compared to last {period}."
        insight_type = "success"
    else:
        insight_message = f"Your energy usage is stable compared to last {period}."
        insight_type = "info"
    
    # Weekly goal progress (simulated)
    weekly_goal_kwh = patterns.get("avg_daily_kwh", 15) * 7 * 0.9  # 10% reduction goal
    current_week_consumption = current_consumption if period == "week" else current_consumption * 7
    goal_progress = min((weekly_goal_kwh - current_week_consumption) / weekly_goal_kwh * 100, 100)
    goal_progress = max(goal_progress, 0)
    
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
            "goal_description": f"This week's energy goal: {goal_progress:.0f}% achieved"
        },
        "chart_data": chart_data,
        "patterns": patterns
    }

# Enhanced AI Assistant endpoint
@api_router.get("/ai-insights")
async def get_ai_insights(user_id: str = Depends(get_current_user)):
    # Get user's recent consumption data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_days_ago}
    }, {"_id": 0}).sort("timestamp", -1).to_list(100)
    
    # Analyze patterns
    patterns = analyze_consumption_patterns(readings)
    
    # Generate personalized insights
    insights = generate_personalized_insights(patterns, user_id)
    
    return {"insights": insights, "patterns": patterns}

# Challenges endpoint
@api_router.get("/challenges")
async def get_challenges(user_id: str = Depends(get_current_user)):
    # Get current consumption for progress calculation
    week_start = datetime.utcnow() - timedelta(days=7)
    recent_readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": week_start}
    }, {"_id": 0}).to_list(100)
    
    current_week_consumption = sum(r["consumption_kwh"] for r in recent_readings)
    
    challenges = [
        {
            "id": "reduce_evening_usage",
            "title": "Evening Energy Challenge",
            "description": "Reduce evening usage (6-9 PM) by 10% this week",
            "target_value": 15.0,  # kWh reduction target
            "current_progress": min(random.uniform(8, 14), 15),
            "deadline": datetime.utcnow() + timedelta(days=5),
            "reward_badge": "evening_saver",
            "active": True
        },
        {
            "id": "weekend_efficiency",
            "title": "Weekend Efficiency Master",
            "description": "Keep weekend usage below weekday average",
            "target_value": 100.0,  # percentage
            "current_progress": random.uniform(70, 95),
            "deadline": datetime.utcnow() + timedelta(days=3),
            "reward_badge": "weekend_warrior",
            "active": True
        },
        {
            "id": "monthly_saver",
            "title": "Monthly Energy Saver",
            "description": "Save €20 compared to last month",
            "target_value": 20.0,  # euros
            "current_progress": random.uniform(8, 18),
            "deadline": datetime.utcnow() + timedelta(days=15),
            "reward_badge": "monthly_champion",
            "active": True
        }
    ]
    
    return {"challenges": challenges}

# Enhanced Badges endpoint
@api_router.get("/badges")
async def get_badges(user_id: str = Depends(get_current_user)):
    all_badges = [
        {
            "id": "energy_saver",
            "name": "Energy Saver",
            "description": "Reduced energy consumption by 10% this month",
            "icon": "🌱",
            "category": "efficiency",
            "unlocked_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "id": "week_warrior",
            "name": "Week Warrior",
            "description": "Stayed under daily target for 7 days straight",
            "icon": "💪",
            "category": "consistency",
            "unlocked_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "id": "early_adopter",
            "name": "Early Adopter",
            "description": "Joined Energo Smart community",
            "icon": "🚀",
            "category": "milestone",
            "unlocked_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "id": "efficiency_expert",
            "name": "Efficiency Expert",
            "description": "Achieved 20% energy reduction",
            "icon": "⚡",
            "category": "efficiency",
            "unlocked_at": None
        },
        {
            "id": "green_champion",
            "name": "Green Champion",
            "description": "Maintained low usage for 30 days",
            "icon": "🏆",
            "category": "achievement",
            "unlocked_at": None
        },
        {
            "id": "cost_cutter",
            "name": "Cost Cutter",
            "description": "Saved €50 in a single month",
            "icon": "💰",
            "category": "savings",
            "unlocked_at": None
        }
    ]
    
    # Calculate some badge unlocks based on user data
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    readings = await db.energy_readings.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_days_ago}
    }, {"_id": 0}).to_list(100)
    
    if len(readings) >= 25:  # Active user
        for badge in all_badges:
            if badge["id"] == "efficiency_expert" and badge["unlocked_at"] is None:
                # Simulate achievement based on data
                avg_consumption = sum(r["consumption_kwh"] for r in readings) / len(readings)
                if avg_consumption < 12:  # Good efficiency
                    badge["unlocked_at"] = datetime.utcnow() - timedelta(days=random.randint(1, 5))
    
    return {"badges": all_badges}

# Settings endpoints
@api_router.get("/settings")
async def get_settings(user_id: str = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"settings": user.get("settings", UserSettings().dict())}

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
    current_plan = settings.get("subscription_plan", "free")
    
    plans = {
        "free": {
            "name": "Free Plan",
            "price": 0,
            "features": [
                "Basic energy tracking",
                "Weekly summaries",
                "3 AI insights per week",
                "Basic badges"
            ],
            "limitations": [
                "Limited historical data (30 days)",
                "Basic insights only"
            ]
        },
        "premium": {
            "name": "Premium Plan",
            "price": 8,
            "features": [
                "Advanced energy analytics",
                "Unlimited AI insights",
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
        "stripe_integration": "placeholder"  # Placeholder for Stripe integration
    }

# Notifications endpoint
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
            "title": "Weekly Summary Ready",
            "message": "Great job! You saved €12 this week compared to last week. View your detailed report.",
            "type": "summary",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "title": "New Badge Earned!",
            "message": "Congratulations! You've unlocked the 'Week Warrior' badge for consistent energy savings.",
            "type": "achievement",
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "read": True
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Challenge Update",
            "message": "You're 80% of the way to completing the Evening Energy Challenge. Keep it up!",
            "type": "challenge",
            "timestamp": datetime.utcnow() - timedelta(days=3),
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()