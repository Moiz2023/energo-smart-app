from models import DeviceTemplate, DeviceType, DeviceCategory, UsageScenario, ScenarioTemplate, PropertyCreate, DeviceCreate, PropertyType, Region, TariffType, ElectricityTariff
from typing import Dict, List
import random

# Device Templates with realistic power consumption data
DEVICE_TEMPLATES: Dict[DeviceType, DeviceTemplate] = {
    # Major Appliances
    DeviceType.REFRIGERATOR: DeviceTemplate(
        device_type=DeviceType.REFRIGERATOR,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Refrigerator",
        typical_wattage=150,
        typical_daily_hours=24,
        typical_weekly_hours=168,
        standby_wattage=120
    ),
    DeviceType.WASHING_MACHINE: DeviceTemplate(
        device_type=DeviceType.WASHING_MACHINE,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Washing Machine",
        typical_wattage=2000,
        typical_daily_hours=1,
        typical_weekly_hours=4,
        standby_wattage=5
    ),
    DeviceType.DISHWASHER: DeviceTemplate(
        device_type=DeviceType.DISHWASHER,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Dishwasher",
        typical_wattage=1800,
        typical_daily_hours=1.5,
        typical_weekly_hours=7,
        standby_wattage=3
    ),
    DeviceType.DRYER: DeviceTemplate(
        device_type=DeviceType.DRYER,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Clothes Dryer",
        typical_wattage=3000,
        typical_daily_hours=0.5,
        typical_weekly_hours=3,
        standby_wattage=2
    ),
    DeviceType.OVEN: DeviceTemplate(
        device_type=DeviceType.OVEN,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Electric Oven",
        typical_wattage=2500,
        typical_daily_hours=1,
        typical_weekly_hours=5,
        standby_wattage=10
    ),
    DeviceType.MICROWAVE: DeviceTemplate(
        device_type=DeviceType.MICROWAVE,
        category=DeviceCategory.MAJOR_APPLIANCES,
        name="Microwave",
        typical_wattage=1200,
        typical_daily_hours=0.5,
        typical_weekly_hours=3,
        standby_wattage=8
    ),
    
    # Electronics
    DeviceType.TV: DeviceTemplate(
        device_type=DeviceType.TV,
        category=DeviceCategory.ELECTRONICS,
        name="LED TV",
        typical_wattage=120,
        typical_daily_hours=6,
        typical_weekly_hours=35,
        standby_wattage=15
    ),
    DeviceType.PC: DeviceTemplate(
        device_type=DeviceType.PC,
        category=DeviceCategory.ELECTRONICS,
        name="Desktop PC",
        typical_wattage=300,
        typical_daily_hours=8,
        typical_weekly_hours=50,
        standby_wattage=20
    ),
    DeviceType.LAPTOP: DeviceTemplate(
        device_type=DeviceType.LAPTOP,
        category=DeviceCategory.ELECTRONICS,
        name="Laptop",
        typical_wattage=65,
        typical_daily_hours=6,
        typical_weekly_hours=35,
        standby_wattage=5
    ),
    DeviceType.GAMING_CONSOLE: DeviceTemplate(
        device_type=DeviceType.GAMING_CONSOLE,
        category=DeviceCategory.ELECTRONICS,
        name="Gaming Console",
        typical_wattage=150,
        typical_daily_hours=3,
        typical_weekly_hours=15,
        standby_wattage=25
    ),
    DeviceType.ROUTER: DeviceTemplate(
        device_type=DeviceType.ROUTER,
        category=DeviceCategory.ELECTRONICS,
        name="WiFi Router",
        typical_wattage=12,
        typical_daily_hours=24,
        typical_weekly_hours=168,
        standby_wattage=12
    ),
    
    # Lighting
    DeviceType.LED_LIGHTS: DeviceTemplate(
        device_type=DeviceType.LED_LIGHTS,
        category=DeviceCategory.LIGHTING,
        name="LED Light Zone",
        typical_wattage=60,
        typical_daily_hours=8,
        typical_weekly_hours=50,
        standby_wattage=0
    ),
    DeviceType.SMART_BULBS: DeviceTemplate(
        device_type=DeviceType.SMART_BULBS,
        category=DeviceCategory.LIGHTING,
        name="Smart Bulbs",
        typical_wattage=45,
        typical_daily_hours=6,
        typical_weekly_hours=35,
        standby_wattage=2
    ),
    DeviceType.OUTDOOR_LIGHTING: DeviceTemplate(
        device_type=DeviceType.OUTDOOR_LIGHTING,
        category=DeviceCategory.LIGHTING,
        name="Outdoor Lighting",
        typical_wattage=100,
        typical_daily_hours=12,
        typical_weekly_hours=84,
        standby_wattage=0
    ),
    
    # Heating/Cooling
    DeviceType.HEAT_PUMP: DeviceTemplate(
        device_type=DeviceType.HEAT_PUMP,
        category=DeviceCategory.HEATING_COOLING,
        name="Heat Pump",
        typical_wattage=3500,
        typical_daily_hours=8,
        typical_weekly_hours=40,
        standby_wattage=50
    ),
    DeviceType.AC_UNIT: DeviceTemplate(
        device_type=DeviceType.AC_UNIT,
        category=DeviceCategory.HEATING_COOLING,
        name="Air Conditioning",
        typical_wattage=2500,
        typical_daily_hours=6,
        typical_weekly_hours=30,
        standby_wattage=20
    ),
    DeviceType.ELECTRIC_HEATER: DeviceTemplate(
        device_type=DeviceType.ELECTRIC_HEATER,
        category=DeviceCategory.HEATING_COOLING,
        name="Electric Heater",
        typical_wattage=1500,
        typical_daily_hours=4,
        typical_weekly_hours=20,
        standby_wattage=0
    ),
    
    # Water Heating
    DeviceType.WATER_HEATER: DeviceTemplate(
        device_type=DeviceType.WATER_HEATER,
        category=DeviceCategory.WATER_HEATING,
        name="Electric Water Heater",
        typical_wattage=4000,
        typical_daily_hours=3,
        typical_weekly_hours=15,
        standby_wattage=100
    ),
    DeviceType.BOILER: DeviceTemplate(
        device_type=DeviceType.BOILER,
        category=DeviceCategory.WATER_HEATING,
        name="Electric Boiler",
        typical_wattage=3000,
        typical_daily_hours=4,
        typical_weekly_hours=25,
        standby_wattage=80
    ),
    
    # EV Charging
    DeviceType.EV_CHARGER: DeviceTemplate(
        device_type=DeviceType.EV_CHARGER,
        category=DeviceCategory.EV_CHARGING,
        name="EV Charger",
        typical_wattage=7400,  # 7.4kW home charger
        typical_daily_hours=2,
        typical_weekly_hours=10,
        standby_wattage=15
    ),
}

# Usage Scenarios with realistic property and device configurations
USAGE_SCENARIOS: Dict[UsageScenario, ScenarioTemplate] = {
    UsageScenario.FAMILY_HOME: ScenarioTemplate(
        scenario=UsageScenario.FAMILY_HOME,
        name="Family Home (4 people)",
        description="Typical Belgian family with 4 people, standard appliances and electronics",
        property_template=PropertyCreate(
            name="Family Home",
            property_type=PropertyType.HOME,
            address="123 Residential Street",
            city="Brussels",
            postal_code="1000",
            region=Region.BRUSSELS,
            square_meters=150,
            occupants=4,
            tariff=ElectricityTariff(
                tariff_type=TariffType.DUAL,
                day_rate=0.28,
                night_rate=0.20,
                fixed_monthly_cost=45.0,
                grid_cost=0.05,
                taxes_percentage=21.0
            ),
            meter_id="BE_FAM_001234"
        ),
        device_templates=[
            DeviceCreate(property_id="", name="Kitchen Fridge", device_type=DeviceType.REFRIGERATOR, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=150, daily_runtime_hours=24, weekly_runtime_hours=168),
            DeviceCreate(property_id="", name="Washing Machine", device_type=DeviceType.WASHING_MACHINE, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=2000, daily_runtime_hours=1, weekly_runtime_hours=5),
            DeviceCreate(property_id="", name="Dishwasher", device_type=DeviceType.DISHWASHER, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=1800, daily_runtime_hours=1.5, weekly_runtime_hours=7),
            DeviceCreate(property_id="", name="Living Room TV", device_type=DeviceType.TV, category=DeviceCategory.ELECTRONICS, estimated_wattage=120, daily_runtime_hours=6, weekly_runtime_hours=35),
            DeviceCreate(property_id="", name="Home PC", device_type=DeviceType.PC, category=DeviceCategory.ELECTRONICS, estimated_wattage=300, daily_runtime_hours=4, weekly_runtime_hours=25),
            DeviceCreate(property_id="", name="Gaming Console", device_type=DeviceType.GAMING_CONSOLE, category=DeviceCategory.ELECTRONICS, estimated_wattage=150, daily_runtime_hours=3, weekly_runtime_hours=15),
            DeviceCreate(property_id="", name="Living Areas Lighting", device_type=DeviceType.LED_LIGHTS, category=DeviceCategory.LIGHTING, estimated_wattage=200, daily_runtime_hours=8, weekly_runtime_hours=50),
            DeviceCreate(property_id="", name="Water Heater", device_type=DeviceType.WATER_HEATER, category=DeviceCategory.WATER_HEATING, estimated_wattage=4000, daily_runtime_hours=3, weekly_runtime_hours=15),
        ],
        typical_monthly_kwh=450,
        typical_monthly_cost=120.0
    ),
    
    UsageScenario.EV_OWNER: ScenarioTemplate(
        scenario=UsageScenario.EV_OWNER,
        name="EV Owner Home",
        description="Modern home with electric vehicle charging and energy-efficient appliances",
        property_template=PropertyCreate(
            name="EV Owner Home",
            property_type=PropertyType.HOME,
            address="456 Green Energy Lane",
            city="Ghent",
            postal_code="9000",
            region=Region.FLANDERS,
            square_meters=180,
            occupants=2,
            tariff=ElectricityTariff(
                tariff_type=TariffType.DYNAMIC,
                single_rate=0.25,
                fixed_monthly_cost=50.0,
                grid_cost=0.06,
                taxes_percentage=21.0
            ),
            meter_id="BE_EV_005678"
        ),
        device_templates=[
            DeviceCreate(property_id="", name="Energy Efficient Fridge", device_type=DeviceType.REFRIGERATOR, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=120, daily_runtime_hours=24, weekly_runtime_hours=168),
            DeviceCreate(property_id="", name="Heat Pump", device_type=DeviceType.HEAT_PUMP, category=DeviceCategory.HEATING_COOLING, estimated_wattage=3500, daily_runtime_hours=6, weekly_runtime_hours=35),
            DeviceCreate(property_id="", name="EV Home Charger", device_type=DeviceType.EV_CHARGER, category=DeviceCategory.EV_CHARGING, estimated_wattage=7400, daily_runtime_hours=3, weekly_runtime_hours=15),
            DeviceCreate(property_id="", name="Smart TV", device_type=DeviceType.TV, category=DeviceCategory.ELECTRONICS, estimated_wattage=100, daily_runtime_hours=5, weekly_runtime_hours=30),
            DeviceCreate(property_id="", name="Home Office Setup", device_type=DeviceType.PC, category=DeviceCategory.ELECTRONICS, estimated_wattage=250, daily_runtime_hours=8, weekly_runtime_hours=40),
            DeviceCreate(property_id="", name="Smart LED Lighting", device_type=DeviceType.SMART_BULBS, category=DeviceCategory.LIGHTING, estimated_wattage=150, daily_runtime_hours=7, weekly_runtime_hours=45),
            DeviceCreate(property_id="", name="Efficient Dishwasher", device_type=DeviceType.DISHWASHER, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=1500, daily_runtime_hours=1, weekly_runtime_hours=6),
        ],
        typical_monthly_kwh=720,
        typical_monthly_cost=185.0
    ),
    
    UsageScenario.SMALL_BUSINESS: ScenarioTemplate(
        scenario=UsageScenario.SMALL_BUSINESS,
        name="Small Office",
        description="Small business office with computers, lighting, and basic amenities",
        property_template=PropertyCreate(
            name="Small Business Office",
            property_type=PropertyType.OFFICE,
            address="789 Business Park",
            city="Antwerp",
            postal_code="2000",
            region=Region.FLANDERS,
            square_meters=120,
            occupants=8,
            tariff=ElectricityTariff(
                tariff_type=TariffType.SINGLE,
                single_rate=0.22,
                fixed_monthly_cost=75.0,
                grid_cost=0.04,
                taxes_percentage=21.0
            ),
            meter_id="BE_BIZ_009012"
        ),
        device_templates=[
            DeviceCreate(property_id="", name="Office Computers (8x)", device_type=DeviceType.PC, category=DeviceCategory.ELECTRONICS, estimated_wattage=2400, daily_runtime_hours=9, weekly_runtime_hours=45),
            DeviceCreate(property_id="", name="LED Office Lighting", device_type=DeviceType.LED_LIGHTS, category=DeviceCategory.LIGHTING, estimated_wattage=300, daily_runtime_hours=10, weekly_runtime_hours=50),
            DeviceCreate(property_id="", name="Office Fridge", device_type=DeviceType.REFRIGERATOR, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=200, daily_runtime_hours=24, weekly_runtime_hours=168),
            DeviceCreate(property_id="", name="Microwave", device_type=DeviceType.MICROWAVE, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=1200, daily_runtime_hours=0.5, weekly_runtime_hours=2.5),
            DeviceCreate(property_id="", name="Network Equipment", device_type=DeviceType.ROUTER, category=DeviceCategory.ELECTRONICS, estimated_wattage=50, daily_runtime_hours=24, weekly_runtime_hours=168),
            DeviceCreate(property_id="", name="AC System", device_type=DeviceType.AC_UNIT, category=DeviceCategory.HEATING_COOLING, estimated_wattage=3000, daily_runtime_hours=6, weekly_runtime_hours=30),
        ],
        typical_monthly_kwh=380,
        typical_monthly_cost=95.0
    ),
    
    UsageScenario.STUDIO_APARTMENT: ScenarioTemplate(
        scenario=UsageScenario.STUDIO_APARTMENT,
        name="Studio Apartment",
        description="Compact living space with essential appliances for 1-2 people",
        property_template=PropertyCreate(
            name="Studio Apartment",
            property_type=PropertyType.HOME,
            address="321 Student Quarter",
            city="Leuven",
            postal_code="3000",
            region=Region.FLANDERS,
            square_meters=45,
            occupants=1,
            tariff=ElectricityTariff(
                tariff_type=TariffType.SINGLE,
                single_rate=0.30,
                fixed_monthly_cost=35.0,
                grid_cost=0.05,
                taxes_percentage=21.0
            ),
            meter_id="BE_STU_003456"
        ),
        device_templates=[
            DeviceCreate(property_id="", name="Compact Fridge", device_type=DeviceType.REFRIGERATOR, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=100, daily_runtime_hours=24, weekly_runtime_hours=168),
            DeviceCreate(property_id="", name="Laptop", device_type=DeviceType.LAPTOP, category=DeviceCategory.ELECTRONICS, estimated_wattage=65, daily_runtime_hours=8, weekly_runtime_hours=50),
            DeviceCreate(property_id="", name="Small TV", device_type=DeviceType.TV, category=DeviceCategory.ELECTRONICS, estimated_wattage=80, daily_runtime_hours=4, weekly_runtime_hours=25),
            DeviceCreate(property_id="", name="Studio Lighting", device_type=DeviceType.LED_LIGHTS, category=DeviceCategory.LIGHTING, estimated_wattage=50, daily_runtime_hours=6, weekly_runtime_hours=35),
            DeviceCreate(property_id="", name="Microwave", device_type=DeviceType.MICROWAVE, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=900, daily_runtime_hours=0.5, weekly_runtime_hours=3),
            DeviceCreate(property_id="", name="Electric Heater", device_type=DeviceType.ELECTRIC_HEATER, category=DeviceCategory.HEATING_COOLING, estimated_wattage=1500, daily_runtime_hours=4, weekly_runtime_hours=25),
        ],
        typical_monthly_kwh=180,
        typical_monthly_cost=65.0
    ),
    
    UsageScenario.SMART_HOME: ScenarioTemplate(
        scenario=UsageScenario.SMART_HOME,
        name="Smart Home",
        description="Technology-forward home with smart devices and energy monitoring",
        property_template=PropertyCreate(
            name="Smart Home",
            property_type=PropertyType.HOME,
            address="555 Tech Valley",
            city="Bruges",
            postal_code="8000",
            region=Region.FLANDERS,
            square_meters=200,
            occupants=3,
            tariff=ElectricityTariff(
                tariff_type=TariffType.DYNAMIC,
                single_rate=0.24,
                fixed_monthly_cost=55.0,
                grid_cost=0.06,
                taxes_percentage=21.0
            ),
            meter_id="BE_SMT_007890"
        ),
        device_templates=[
            DeviceCreate(property_id="", name="Smart Fridge", device_type=DeviceType.REFRIGERATOR, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=140, daily_runtime_hours=24, weekly_runtime_hours=168, smart_integration_id="smart_plug_01"),
            DeviceCreate(property_id="", name="Smart Heat Pump", device_type=DeviceType.HEAT_PUMP, category=DeviceCategory.HEATING_COOLING, estimated_wattage=3200, daily_runtime_hours=7, weekly_runtime_hours=40, smart_integration_id="smart_plug_02"),
            DeviceCreate(property_id="", name="Home Server", device_type=DeviceType.PC, category=DeviceCategory.ELECTRONICS, estimated_wattage=200, daily_runtime_hours=24, weekly_runtime_hours=168, smart_integration_id="smart_plug_03"),
            DeviceCreate(property_id="", name="Smart Lighting System", device_type=DeviceType.SMART_BULBS, category=DeviceCategory.LIGHTING, estimated_wattage=180, daily_runtime_hours=8, weekly_runtime_hours=50, smart_integration_id="smart_switch_01"),
            DeviceCreate(property_id="", name="Gaming Setup", device_type=DeviceType.GAMING_CONSOLE, category=DeviceCategory.ELECTRONICS, estimated_wattage=180, daily_runtime_hours=4, weekly_runtime_hours=20, smart_integration_id="smart_plug_04"),
            DeviceCreate(property_id="", name="Smart Dishwasher", device_type=DeviceType.DISHWASHER, category=DeviceCategory.MAJOR_APPLIANCES, estimated_wattage=1600, daily_runtime_hours=1.5, weekly_runtime_hours=8, smart_integration_id="smart_plug_05"),
        ],
        typical_monthly_kwh=520,
        typical_monthly_cost=140.0
    )
}

def get_device_template(device_type: DeviceType) -> DeviceTemplate:
    """Get device template by type"""
    return DEVICE_TEMPLATES.get(device_type)

def get_scenario_template(scenario: UsageScenario) -> ScenarioTemplate:
    """Get usage scenario template"""
    return USAGE_SCENARIOS.get(scenario)

def get_common_devices() -> List[DeviceTemplate]:
    """Get list of most common devices for quick-add"""
    common_types = [
        DeviceType.REFRIGERATOR,
        DeviceType.WASHING_MACHINE,
        DeviceType.DISHWASHER,
        DeviceType.WATER_HEATER,
        DeviceType.EV_CHARGER,
        DeviceType.TV,
        DeviceType.PC,
        DeviceType.GAMING_CONSOLE,
        DeviceType.LED_LIGHTS
    ]
    return [DEVICE_TEMPLATES[dt] for dt in common_types if dt in DEVICE_TEMPLATES]

def get_devices_by_category(category: DeviceCategory) -> List[DeviceTemplate]:
    """Get devices filtered by category"""
    return [template for template in DEVICE_TEMPLATES.values() if template.category == category]

def generate_realistic_consumption_variation(base_wattage: int, hours: float) -> float:
    """Generate realistic consumption with variation"""
    # Add ±15% variation to simulate real-world conditions
    variation = random.uniform(0.85, 1.15)
    return (base_wattage * hours * variation) / 1000  # Convert to kWh