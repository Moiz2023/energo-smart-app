from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid

# Property Models
class PropertyType(str, Enum):
    HOME = "home"
    OFFICE = "office"
    RENTAL = "rental"
    VACATION = "vacation"
    OTHER = "other"

class Region(str, Enum):
    BRUSSELS = "brussels"
    FLANDERS = "flanders"
    WALLONIA = "wallonia"

class TariffType(str, Enum):
    SINGLE = "single"  # Single rate
    DUAL = "dual"      # Day/Night rates
    DYNAMIC = "dynamic" # Dynamic pricing

class ElectricityTariff(BaseModel):
    tariff_type: TariffType = TariffType.SINGLE
    single_rate: Optional[float] = None  # €/kWh
    day_rate: Optional[float] = None     # €/kWh
    night_rate: Optional[float] = None   # €/kWh
    peak_rate: Optional[float] = None    # €/kWh
    off_peak_rate: Optional[float] = None # €/kWh
    fixed_monthly_cost: float = 0.0      # Fixed monthly costs
    grid_cost: float = 0.0               # Grid costs €/kWh
    taxes_percentage: float = 21.0       # VAT and other taxes %

class PropertyCreate(BaseModel):
    name: str
    property_type: PropertyType
    address: str
    city: str
    postal_code: str
    region: Region
    timezone: str = "Europe/Brussels"
    square_meters: Optional[int] = None
    occupants: Optional[int] = None
    tariff: ElectricityTariff
    meter_id: Optional[str] = None  # Smart meter ID
    api_provider: Optional[str] = None  # fluvius, luminus, engie
    
class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[PropertyType] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    region: Optional[Region] = None
    timezone: Optional[str] = None
    square_meters: Optional[int] = None
    occupants: Optional[int] = None
    tariff: Optional[ElectricityTariff] = None
    meter_id: Optional[str] = None
    api_provider: Optional[str] = None

class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    property_type: PropertyType
    address: str
    city: str
    postal_code: str
    region: Region
    timezone: str
    square_meters: Optional[int] = None
    occupants: Optional[int] = None
    tariff: ElectricityTariff
    meter_id: Optional[str] = None
    api_provider: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

# Device Models
class DeviceCategory(str, Enum):
    MAJOR_APPLIANCES = "major_appliances"
    ELECTRONICS = "electronics" 
    LIGHTING = "lighting"
    HEATING_COOLING = "heating_cooling"
    WATER_HEATING = "water_heating"
    EV_CHARGING = "ev_charging"
    OTHER = "other"

class DeviceType(str, Enum):
    # Major Appliances
    REFRIGERATOR = "refrigerator"
    WASHING_MACHINE = "washing_machine"
    DISHWASHER = "dishwasher"
    DRYER = "dryer"
    OVEN = "oven"
    MICROWAVE = "microwave"
    
    # Electronics
    TV = "tv"
    PC = "pc"
    LAPTOP = "laptop"
    GAMING_CONSOLE = "gaming_console"
    ROUTER = "router"
    
    # Lighting
    LED_LIGHTS = "led_lights"
    SMART_BULBS = "smart_bulbs"
    OUTDOOR_LIGHTING = "outdoor_lighting"
    
    # Heating/Cooling
    HEAT_PUMP = "heat_pump"
    AC_UNIT = "ac_unit"
    ELECTRIC_HEATER = "electric_heater"
    
    # Water Heating
    WATER_HEATER = "water_heater"
    BOILER = "boiler"
    
    # EV Charging
    EV_CHARGER = "ev_charger"
    
    # Other
    OTHER = "other"

class EnergyRating(str, Enum):
    A_PLUS_PLUS_PLUS = "A+++"
    A_PLUS_PLUS = "A++"
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

class DeviceTemplate(BaseModel):
    device_type: DeviceType
    category: DeviceCategory
    name: str
    typical_wattage: int  # Watts
    typical_daily_hours: float  # Hours per day
    typical_weekly_hours: float  # Hours per week
    standby_wattage: int = 0  # Standby power consumption

class DeviceCreate(BaseModel):
    property_id: str
    name: str
    device_type: DeviceType
    category: DeviceCategory
    estimated_wattage: int  # Watts
    standby_wattage: int = 0
    daily_runtime_hours: float = 0.0
    weekly_runtime_hours: float = 0.0
    brand: Optional[str] = None
    model: Optional[str] = None
    energy_rating: Optional[EnergyRating] = None
    smart_integration_id: Optional[str] = None  # Smart plug ID, local submeter channel
    notes: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    estimated_wattage: Optional[int] = None
    standby_wattage: Optional[int] = None
    daily_runtime_hours: Optional[float] = None
    weekly_runtime_hours: Optional[float] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    energy_rating: Optional[EnergyRating] = None
    smart_integration_id: Optional[str] = None
    notes: Optional[str] = None

class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    user_id: str
    name: str
    device_type: DeviceType
    category: DeviceCategory
    estimated_wattage: int
    standby_wattage: int = 0
    daily_runtime_hours: float = 0.0
    weekly_runtime_hours: float = 0.0
    brand: Optional[str] = None
    model: Optional[str] = None
    energy_rating: Optional[EnergyRating] = None
    smart_integration_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

# Meter Reading Models
class MeterReadingSource(str, Enum):
    MANUAL = "manual"
    API_FLUVIUS = "api_fluvius"
    API_LUMINUS = "api_luminus"
    API_ENGIE = "api_engie"
    CSV_UPLOAD = "csv_upload"
    P1_DONGLE = "p1_dongle"
    SIMULATED = "simulated"

class MeterReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    user_id: str
    meter_id: str
    timestamp: datetime
    consumption_kwh: float
    production_kwh: float = 0.0  # Solar/renewable production
    cost_euros: Optional[float] = None
    tariff_rate: Optional[float] = None  # Rate at time of reading
    source: MeterReadingSource = MeterReadingSource.MANUAL
    raw_data: Optional[Dict[str, Any]] = None  # Store original API response
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MeterReadingCreate(BaseModel):
    property_id: str
    meter_id: str
    timestamp: datetime
    consumption_kwh: float
    production_kwh: float = 0.0
    cost_euros: Optional[float] = None
    tariff_rate: Optional[float] = None
    source: MeterReadingSource = MeterReadingSource.MANUAL
    raw_data: Optional[Dict[str, Any]] = None

# Device Consumption Analysis Models
class DeviceConsumptionEstimate(BaseModel):
    device_id: str
    device_name: str
    estimated_daily_kwh: float
    estimated_weekly_kwh: float
    estimated_monthly_kwh: float
    estimated_daily_cost: float
    estimated_weekly_cost: float
    estimated_monthly_cost: float
    confidence_score: float  # 0.0 to 1.0

class ConsumptionDiscrepancy(BaseModel):
    property_id: str
    timestamp: datetime
    total_estimated_kwh: float
    actual_metered_kwh: float
    discrepancy_kwh: float
    discrepancy_percentage: float
    unaccounted_consumption: float
    alert_level: str  # low, medium, high
    description: str

class DeviceAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    device_id: Optional[str] = None
    alert_type: str  # high_consumption, abnormal_pattern, device_offline, calibration_needed
    severity: str  # info, warning, error
    title: str
    message: str
    estimated_impact_kwh: Optional[float] = None
    estimated_impact_cost: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False

# Usage Scenario Models (for demo/testing)
class UsageScenario(str, Enum):
    FAMILY_HOME = "family_home"
    EV_OWNER = "ev_owner"
    SMALL_BUSINESS = "small_business"
    STUDIO_APARTMENT = "studio_apartment"
    SMART_HOME = "smart_home"

class ScenarioTemplate(BaseModel):
    scenario: UsageScenario
    name: str
    description: str
    property_template: PropertyCreate
    device_templates: List[DeviceCreate]
    typical_monthly_kwh: float
    typical_monthly_cost: float

# CSV Upload Models
class CSVUploadRequest(BaseModel):
    property_id: str
    filename: str
    data_format: str  # hourly, daily, monthly
    timezone: str = "Europe/Brussels"
    
class CSVMeterData(BaseModel):
    timestamp: datetime
    consumption_kwh: float
    production_kwh: float = 0.0

# API Integration Models
class APIProviderConfig(BaseModel):
    provider: str  # fluvius, luminus, engie
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    refresh_token: Optional[str] = None
    meter_id: str
    active: bool = True
    last_sync: Optional[datetime] = None
    
class PropertyAPIConfig(BaseModel):
    property_id: str
    provider_configs: List[APIProviderConfig]

# Dashboard Models
class PropertyDashboard(BaseModel):
    property: Property
    devices: List[Device]
    device_estimates: List[DeviceConsumptionEstimate] 
    recent_readings: List[MeterReading]
    alerts: List[DeviceAlert]
    monthly_summary: Dict[str, Any]
    discrepancies: List[ConsumptionDiscrepancy]

class DeviceCalibration(BaseModel):
    device_id: str
    calibration_method: str  # smart_plug, manual_confirmation, runtime_adjustment
    actual_consumption_kwh: float
    measurement_period_hours: float
    calibrated_wattage: int
    confidence_score: float
    calibrated_at: datetime = Field(default_factory=datetime.utcnow)