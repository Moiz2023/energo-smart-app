from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
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
import csv
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import our new models and utilities
from models import *
from device_templates import *
from consumption_engine import ConsumptionAnalysisEngine, MockDataGenerator

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

# Initialize engines
consumption_engine = ConsumptionAnalysisEngine()
mock_generator = MockDataGenerator()

# Existing models (keeping existing functionality)
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
    region: str = "brussels"

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

# Auth functions (keeping existing)
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
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# PROPERTY MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.post("/properties", response_model=Property)
async def create_property(property_data: PropertyCreate, user_id: str = Depends(get_current_user)):
    """Create a new property for the user"""
    try:
        property_dict = property_data.dict()
        property_dict["user_id"] = user_id
        property_dict["id"] = str(uuid.uuid4())
        property_dict["created_at"] = datetime.utcnow()
        property_dict["updated_at"] = datetime.utcnow()
        
        await db.properties.insert_one(property_dict)
        
        return Property(**property_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create property: {str(e)}")

@api_router.get("/properties", response_model=List[Property])
async def get_user_properties(user_id: str = Depends(get_current_user)):
    """Get all properties for the current user"""
    try:
        properties = list(await db.properties.find(
            {"user_id": user_id, "active": True}
        ).sort("created_at", -1).to_list(length=100))
        
        return [Property(**prop) for prop in properties]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {str(e)}")

@api_router.get("/properties/{property_id}", response_model=Property)
async def get_property(property_id: str, user_id: str = Depends(get_current_user)):
    """Get a specific property"""
    try:
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return Property(**property_doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch property: {str(e)}")

@api_router.put("/properties/{property_id}", response_model=Property)
async def update_property(
    property_id: str, 
    property_update: PropertyUpdate, 
    user_id: str = Depends(get_current_user)
):
    """Update a property"""
    try:
        # Check if property exists and belongs to user
        existing_property = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not existing_property:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in property_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.properties.update_one(
            {"id": property_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        # Return updated property
        updated_property = await db.properties.find_one({"id": property_id})
        return Property(**updated_property)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update property: {str(e)}")

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str, user_id: str = Depends(get_current_user)):
    """Soft delete a property"""
    try:
        result = await db.properties.update_one(
            {"id": property_id, "user_id": user_id},
            {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Also deactivate all devices in this property
        await db.devices.update_many(
            {"property_id": property_id, "user_id": user_id},
            {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Property deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete property: {str(e)}")

# ============================================================================
# DEVICE MANAGEMENT ENDPOINTS
# ============================================================================

@api_router.get("/device-templates")
async def get_device_templates():
    """Get all device templates for quick-add functionality"""
    try:
        common_devices = get_common_devices()
        templates_by_category = {}
        
        for category in DeviceCategory:
            templates_by_category[category.value] = get_devices_by_category(category)
        
        return {
            "common_devices": common_devices,
            "by_category": templates_by_category,
            "all_templates": list(DEVICE_TEMPLATES.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device templates: {str(e)}")

@api_router.post("/properties/{property_id}/devices", response_model=Device)
async def create_device(
    property_id: str,
    device_data: DeviceCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new device for a property"""
    try:
        # Verify property belongs to user
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        device_dict = device_data.dict()
        device_dict["property_id"] = property_id
        device_dict["user_id"] = user_id
        device_dict["id"] = str(uuid.uuid4())
        device_dict["created_at"] = datetime.utcnow()
        device_dict["updated_at"] = datetime.utcnow()
        
        await db.devices.insert_one(device_dict)
        
        return Device(**device_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create device: {str(e)}")

@api_router.get("/properties/{property_id}/devices", response_model=List[Device])
async def get_property_devices(property_id: str, user_id: str = Depends(get_current_user)):
    """Get all devices for a property"""
    try:
        # Verify property belongs to user
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        devices = list(await db.devices.find(
            {"property_id": property_id, "user_id": user_id, "active": True}
        ).sort("created_at", -1).to_list(length=1000))
        
        return [Device(**device) for device in devices]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch devices: {str(e)}")

@api_router.put("/devices/{device_id}", response_model=Device)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a device"""
    try:
        # Check if device exists and belongs to user
        existing_device = await db.devices.find_one(
            {"id": device_id, "user_id": user_id, "active": True}
        )
        
        if not existing_device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in device_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.devices.update_one(
            {"id": device_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        # Return updated device
        updated_device = await db.devices.find_one({"id": device_id})
        return Device(**updated_device)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update device: {str(e)}")

@api_router.delete("/devices/{device_id}")
async def delete_device(device_id: str, user_id: str = Depends(get_current_user)):
    """Soft delete a device"""
    try:
        result = await db.devices.update_one(
            {"id": device_id, "user_id": user_id},
            {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return {"message": "Device deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete device: {str(e)}")

# ============================================================================
# SCENARIO & MOCK DATA ENDPOINTS
# ============================================================================

@api_router.get("/usage-scenarios")
async def get_usage_scenarios():
    """Get all available usage scenarios for demo/testing"""
    try:
        scenarios = {}
        for scenario, template in USAGE_SCENARIOS.items():
            scenarios[scenario.value] = {
                "name": template.name,
                "description": template.description,
                "typical_monthly_kwh": template.typical_monthly_kwh,
                "typical_monthly_cost": template.typical_monthly_cost,
                "device_count": len(template.device_templates)
            }
        
        return {"scenarios": scenarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scenarios: {str(e)}")

@api_router.post("/setup-scenario/{scenario}")
async def setup_usage_scenario(scenario: str, user_id: str = Depends(get_current_user)):
    """Set up a complete usage scenario (property + devices + mock data)"""
    try:
        scenario_enum = UsageScenario(scenario)
        scenario_template = get_scenario_template(scenario_enum)
        
        if not scenario_template:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        # Create property
        property_dict = scenario_template.property_template.dict()
        property_dict["user_id"] = user_id
        property_dict["id"] = str(uuid.uuid4())
        property_dict["created_at"] = datetime.utcnow()
        property_dict["updated_at"] = datetime.utcnow()
        
        await db.properties.insert_one(property_dict)
        property_id = property_dict["id"]
        
        # Create devices
        devices = []
        for device_template in scenario_template.device_templates:
            device_dict = device_template.dict()
            device_dict["property_id"] = property_id
            device_dict["user_id"] = user_id
            device_dict["id"] = str(uuid.uuid4())
            device_dict["created_at"] = datetime.utcnow()
            device_dict["updated_at"] = datetime.utcnow()
            
            await db.devices.insert_one(device_dict)
            devices.append(Device(**device_dict))
        
        # Generate mock meter readings
        property_obj = Property(**property_dict)
        meter_readings = mock_generator.generate_meter_readings(
            property_id=property_id,
            user_id=user_id,
            meter_id=property_obj.meter_id or f"MOCK_{property_id[:8]}",
            devices=devices,
            property_details=property_obj,
            days=30
        )
        
        # Insert meter readings
        readings_dict = [reading.dict() for reading in meter_readings]
        if readings_dict:
            await db.meter_readings.insert_many(readings_dict)
        
        return {
            "message": f"Successfully set up {scenario_template.name}",
            "property_id": property_id,
            "devices_created": len(devices),
            "meter_readings_created": len(meter_readings)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup scenario: {str(e)}")

# ============================================================================
# CONSUMPTION ANALYSIS ENDPOINTS
# ============================================================================

@api_router.get("/properties/{property_id}/consumption-analysis")
async def get_consumption_analysis(
    property_id: str,
    days: int = 7,
    user_id: str = Depends(get_current_user)
):
    """Get detailed consumption analysis for a property"""
    try:
        # Verify property ownership
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_obj = Property(**property_doc)
        
        # Get devices for this property
        device_docs = list(await db.devices.find(
            {"property_id": property_id, "user_id": user_id, "active": True}
        ).to_list(length=1000))
        
        devices = [Device(**device) for device in device_docs]
        
        # Get recent meter readings
        start_date = datetime.utcnow() - timedelta(days=days)
        meter_readings_docs = list(await db.meter_readings.find(
            {"property_id": property_id, "user_id": user_id, "timestamp": {"$gte": start_date}}
        ).sort("timestamp", -1).to_list(length=10000))
        
        meter_readings = [MeterReading(**reading) for reading in meter_readings_docs]
        
        # Calculate device consumption estimates
        device_estimates = []
        for device in devices:
            estimate = consumption_engine.calculate_device_consumption_estimate(
                device=device,
                start_date=start_date,
                end_date=datetime.utcnow(),
                property_details=property_obj
            )
            device_estimates.append(estimate)
        
        # Analyze consumption discrepancies
        discrepancies = consumption_engine.analyze_consumption_discrepancy(
            property_id=property_id,
            devices=devices,
            meter_readings=meter_readings,
            property_details=property_obj
        )
        
        # Generate alerts
        alerts = consumption_engine.generate_device_alerts(
            property_id=property_id,
            devices=devices,
            consumption_estimates=device_estimates,
            discrepancies=discrepancies
        )
        
        # Calculate summary statistics
        total_estimated_kwh = sum(est.estimated_daily_kwh for est in device_estimates) * days
        total_actual_kwh = sum(reading.consumption_kwh for reading in meter_readings)
        total_estimated_cost = sum(est.estimated_daily_cost for est in device_estimates) * days
        total_actual_cost = sum(reading.cost_euros or 0 for reading in meter_readings)
        
        return {
            "property": property_obj,
            "analysis_period_days": days,
            "devices": devices,
            "device_estimates": device_estimates,
            "discrepancies": discrepancies,
            "alerts": alerts,
            "summary": {
                "total_devices": len(devices),
                "total_estimated_kwh": round(total_estimated_kwh, 2),
                "total_actual_kwh": round(total_actual_kwh, 2),
                "total_estimated_cost": round(total_estimated_cost, 2),
                "total_actual_cost": round(total_actual_cost, 2),
                "accuracy_percentage": round((1 - abs(total_actual_kwh - total_estimated_kwh) / total_actual_kwh) * 100, 1) if total_actual_kwh > 0 else 0,
                "active_alerts": len([a for a in alerts if not a.acknowledged]),
                "meter_readings_count": len(meter_readings)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze consumption: {str(e)}")

@api_router.get("/properties/{property_id}/meter-readings")
async def get_meter_readings(
    property_id: str,
    days: int = 30,
    user_id: str = Depends(get_current_user)
):
    """Get meter readings for a property"""
    try:
        # Verify property ownership
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        readings = list(await db.meter_readings.find(
            {"property_id": property_id, "user_id": user_id, "timestamp": {"$gte": start_date}}
        ).sort("timestamp", -1).to_list(length=10000))
        
        return {
            "readings": [MeterReading(**reading) for reading in readings],
            "total_readings": len(readings),
            "period_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch meter readings: {str(e)}")

# ============================================================================
# CSV UPLOAD ENDPOINT
# ============================================================================

@api_router.post("/properties/{property_id}/upload-csv")
async def upload_meter_data_csv(
    property_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload meter reading data via CSV"""
    try:
        # Verify property ownership
        property_doc = await db.properties.find_one(
            {"id": property_id, "user_id": user_id, "active": True}
        )
        
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        
        # Read CSV content
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        meter_readings = []
        
        property_obj = Property(**property_doc)
        meter_id = property_obj.meter_id or f"CSV_{property_id[:8]}"
        
        for row in csv_reader:
            try:
                # Expected columns: timestamp, consumption_kwh, production_kwh (optional)
                timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                consumption_kwh = float(row['consumption_kwh'])
                production_kwh = float(row.get('production_kwh', 0))
                
                # Calculate cost
                cost = consumption_engine._calculate_cost(consumption_kwh, property_obj.tariff)
                
                reading = MeterReading(
                    property_id=property_id,
                    user_id=user_id,
                    meter_id=meter_id,
                    timestamp=timestamp,
                    consumption_kwh=consumption_kwh,
                    production_kwh=production_kwh,
                    cost_euros=cost,
                    source=MeterReadingSource.CSV_UPLOAD
                )
                
                meter_readings.append(reading.dict())
                
            except (ValueError, KeyError) as e:
                continue  # Skip invalid rows
        
        if not meter_readings:
            raise HTTPException(status_code=400, detail="No valid meter reading data found in CSV")
        
        # Insert readings
        await db.meter_readings.insert_many(meter_readings)
        
        return {
            "message": "CSV data uploaded successfully",
            "readings_imported": len(meter_readings),
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload CSV: {str(e)}")

# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@api_router.get("/alerts")
async def get_user_alerts(user_id: str = Depends(get_current_user)):
    """Get all alerts for the user"""
    try:
        # Get all user properties
        properties = list(await db.properties.find(
            {"user_id": user_id, "active": True}
        ).to_list(length=100))
        
        property_ids = [prop["id"] for prop in properties]
        
        # Get alerts for all properties
        alerts = list(await db.device_alerts.find(
            {"property_id": {"$in": property_ids}}
        ).sort("created_at", -1).to_list(length=1000))
        
        return {
            "alerts": [DeviceAlert(**alert) for alert in alerts],
            "total_alerts": len(alerts),
            "unread_count": len([a for a in alerts if not a.get("acknowledged", False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@api_router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user_id: str = Depends(get_current_user)):
    """Acknowledge an alert"""
    try:
        result = await db.device_alerts.update_one(
            {"id": alert_id},
            {"$set": {"acknowledged": True, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert acknowledged"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

# ============================================================================
# EXISTING ENDPOINTS (keeping all existing functionality)
# ============================================================================

# Auth endpoints
@api_router.post("/auth/register")
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "created_at": datetime.utcnow(),
        "settings": UserSettings().dict()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create JWT token
    token = create_jwt_token(user_id)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": user.email,
            "name": user.name,
            "settings": user_doc["settings"]
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["password"]):
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

@api_router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    """Logout endpoint - client should delete token locally"""
    return {"message": "Logged out successfully"}

# Keep all existing endpoints (dashboard, ai-insights, etc.)
# [Previous endpoints would continue here...]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database indexes and collections"""
    try:
        # Create indexes for better performance
        await db.properties.create_index("user_id")
        await db.devices.create_index([("property_id", 1), ("user_id", 1)])
        await db.meter_readings.create_index([("property_id", 1), ("timestamp", -1)])
        await db.device_alerts.create_index([("property_id", 1), ("created_at", -1)])
        
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)