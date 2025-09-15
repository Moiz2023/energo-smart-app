from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from models import (
    Device, MeterReading, DeviceConsumptionEstimate, ConsumptionDiscrepancy, 
    DeviceAlert, Property, MeterReadingSource, ElectricityTariff, TariffType
)
import random
import math

class ConsumptionAnalysisEngine:
    """Engine for analyzing device consumption vs meter readings"""
    
    def __init__(self):
        self.seasonal_factors = {
            1: 1.3,   # January - high heating
            2: 1.2,   # February
            3: 1.1,   # March
            4: 0.9,   # April
            5: 0.8,   # May
            6: 0.8,   # June
            7: 0.9,   # July - AC usage
            8: 0.9,   # August
            9: 0.8,   # September
            10: 0.9,  # October
            11: 1.1,  # November
            12: 1.3   # December - high heating
        }
    
    def calculate_device_consumption_estimate(
        self, 
        device: Device, 
        start_date: datetime, 
        end_date: datetime,
        property_details: Property
    ) -> DeviceConsumptionEstimate:
        """Calculate estimated consumption for a device over a period"""
        
        days = (end_date - start_date).days
        if days == 0:
            days = 1
            
        # Base consumption calculation
        daily_kwh = (device.estimated_wattage * device.daily_runtime_hours) / 1000
        standby_kwh = (device.standby_wattage * (24 - device.daily_runtime_hours)) / 1000
        total_daily_kwh = daily_kwh + standby_kwh
        
        # Apply seasonal factors for heating/cooling devices
        month = start_date.month
        seasonal_factor = 1.0
        if device.category.value in ['heating_cooling', 'water_heating']:
            seasonal_factor = self.seasonal_factors.get(month, 1.0)
        
        # Apply occupancy factor
        occupancy_factor = 1.0
        if property_details.occupants:
            if property_details.occupants > 4:
                occupancy_factor = 1.2
            elif property_details.occupants < 2:
                occupancy_factor = 0.8
        
        # Calculate estimates
        adjusted_daily_kwh = total_daily_kwh * seasonal_factor * occupancy_factor
        weekly_kwh = adjusted_daily_kwh * 7
        monthly_kwh = adjusted_daily_kwh * 30
        
        # Calculate costs based on tariff
        daily_cost = self._calculate_cost(adjusted_daily_kwh, property_details.tariff)
        weekly_cost = self._calculate_cost(weekly_kwh, property_details.tariff)
        monthly_cost = self._calculate_cost(monthly_kwh, property_details.tariff)
        
        # Confidence score based on data quality
        confidence_score = self._calculate_confidence_score(device)
        
        return DeviceConsumptionEstimate(
            device_id=device.id,
            device_name=device.name,
            estimated_daily_kwh=round(adjusted_daily_kwh, 3),
            estimated_weekly_kwh=round(weekly_kwh, 3),
            estimated_monthly_kwh=round(monthly_kwh, 3),
            estimated_daily_cost=round(daily_cost, 2),
            estimated_weekly_cost=round(weekly_cost, 2),
            estimated_monthly_cost=round(monthly_cost, 2),
            confidence_score=confidence_score
        )
    
    def analyze_consumption_discrepancy(
        self,
        property_id: str,
        devices: List[Device],
        meter_readings: List[MeterReading],
        property_details: Property,
        analysis_period_hours: int = 24
    ) -> List[ConsumptionDiscrepancy]:
        """Analyze discrepancies between estimated and actual consumption"""
        
        discrepancies = []
        
        if not meter_readings:
            return discrepancies
        
        # Group meter readings by day
        daily_readings = self._group_readings_by_day(meter_readings)
        
        for date, readings in daily_readings.items():
            if len(readings) < 2:  # Need at least 2 readings for comparison
                continue
                
            # Calculate actual consumption for the day
            actual_kwh = sum(reading.consumption_kwh for reading in readings)
            
            # Calculate total estimated consumption for all devices
            total_estimated_kwh = 0
            for device in devices:
                if device.active:
                    estimate = self.calculate_device_consumption_estimate(
                        device, date, date + timedelta(days=1), property_details
                    )
                    total_estimated_kwh += estimate.estimated_daily_kwh
            
            # Calculate discrepancy
            discrepancy_kwh = actual_kwh - total_estimated_kwh
            discrepancy_percentage = (discrepancy_kwh / total_estimated_kwh * 100) if total_estimated_kwh > 0 else 0
            
            # Determine alert level
            alert_level = "low"
            if abs(discrepancy_percentage) > 30:
                alert_level = "high"
            elif abs(discrepancy_percentage) > 15:
                alert_level = "medium"
            
            # Create description
            if discrepancy_kwh > 0:
                description = f"Unaccounted consumption of {discrepancy_kwh:.2f} kWh detected"
            else:
                description = f"Devices consuming {abs(discrepancy_kwh):.2f} kWh less than metered"
            
            discrepancy = ConsumptionDiscrepancy(
                property_id=property_id,
                timestamp=date,
                total_estimated_kwh=round(total_estimated_kwh, 3),
                actual_metered_kwh=round(actual_kwh, 3),
                discrepancy_kwh=round(discrepancy_kwh, 3),
                discrepancy_percentage=round(discrepancy_percentage, 1),
                unaccounted_consumption=max(0, discrepancy_kwh),
                alert_level=alert_level,
                description=description
            )
            
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    def generate_device_alerts(
        self,
        property_id: str,
        devices: List[Device],
        consumption_estimates: List[DeviceConsumptionEstimate],
        discrepancies: List[ConsumptionDiscrepancy]
    ) -> List[DeviceAlert]:
        """Generate alerts based on consumption analysis"""
        
        alerts = []
        
        # High consumption alerts
        for estimate in consumption_estimates:
            device = next((d for d in devices if d.id == estimate.device_id), None)
            if not device:
                continue
                
            # Check for unusually high consumption
            expected_monthly_kwh = self._get_expected_monthly_consumption(device)
            if estimate.estimated_monthly_kwh > expected_monthly_kwh * 1.3:
                alert = DeviceAlert(
                    property_id=property_id,
                    device_id=device.id,
                    alert_type="high_consumption",
                    severity="warning",
                    title=f"{device.name} - High Consumption Alert",
                    message=f"{device.name} is consuming {estimate.estimated_monthly_kwh:.1f} kWh/month, which is 30% above expected usage.",
                    estimated_impact_kwh=estimate.estimated_monthly_kwh - expected_monthly_kwh,
                    estimated_impact_cost=estimate.estimated_monthly_cost * 0.3
                )
                alerts.append(alert)
        
        # Discrepancy alerts
        for discrepancy in discrepancies:
            if discrepancy.alert_level in ["medium", "high"] and discrepancy.unaccounted_consumption > 1.0:
                severity = "error" if discrepancy.alert_level == "high" else "warning"
                alert = DeviceAlert(
                    property_id=property_id,
                    alert_type="abnormal_pattern",
                    severity=severity,
                    title="Unaccounted Energy Usage",
                    message=f"Detected {discrepancy.unaccounted_consumption:.2f} kWh of unaccounted consumption. This could indicate unknown devices or measurement errors.",
                    estimated_impact_kwh=discrepancy.unaccounted_consumption,
                    estimated_impact_cost=discrepancy.unaccounted_consumption * 0.25  # Avg cost per kWh
                )
                alerts.append(alert)
        
        # Calibration needed alerts
        for estimate in consumption_estimates:
            if estimate.confidence_score < 0.6:
                device = next((d for d in devices if d.id == estimate.device_id), None)
                if device:
                    alert = DeviceAlert(
                        property_id=property_id,
                        device_id=device.id,
                        alert_type="calibration_needed",
                        severity="info",
                        title=f"{device.name} - Calibration Recommended",
                        message=f"The consumption estimate for {device.name} has low confidence. Consider connecting a smart plug or validating runtime hours for better accuracy."
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _calculate_cost(self, kwh: float, tariff: ElectricityTariff) -> float:
        """Calculate cost based on electricity tariff"""
        
        if tariff.tariff_type == TariffType.SINGLE:
            rate = tariff.single_rate or 0.25
        elif tariff.tariff_type == TariffType.DUAL:
            # Assume 60% day rate, 40% night rate
            day_rate = tariff.day_rate or 0.28
            night_rate = tariff.night_rate or 0.20
            rate = (day_rate * 0.6) + (night_rate * 0.4)
        else:  # DYNAMIC
            rate = tariff.single_rate or 0.24
        
        energy_cost = kwh * rate
        grid_cost = kwh * tariff.grid_cost
        total_before_tax = energy_cost + grid_cost
        tax_amount = total_before_tax * (tariff.taxes_percentage / 100)
        
        return total_before_tax + tax_amount
    
    def _calculate_confidence_score(self, device: Device) -> float:
        """Calculate confidence score for consumption estimate"""
        score = 0.5  # Base score
        
        # Increase score if we have smart integration
        if device.smart_integration_id:
            score += 0.3
        
        # Increase score if we have detailed device info
        if device.brand and device.model:
            score += 0.1
        
        if device.energy_rating:
            score += 0.1
        
        # Increase score based on runtime accuracy
        if device.daily_runtime_hours > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _get_expected_monthly_consumption(self, device: Device) -> float:
        """Get expected monthly consumption for device type"""
        # This would typically come from a database of device benchmarks
        base_monthly_kwh = (device.estimated_wattage * device.daily_runtime_hours * 30) / 1000
        return base_monthly_kwh
    
    def _group_readings_by_day(self, readings: List[MeterReading]) -> Dict[datetime, List[MeterReading]]:
        """Group meter readings by day"""
        grouped = {}
        
        for reading in readings:
            day = reading.timestamp.date()
            day_datetime = datetime.combine(day, datetime.min.time())
            
            if day_datetime not in grouped:
                grouped[day_datetime] = []
            grouped[day_datetime].append(reading)
        
        return grouped

class MockDataGenerator:
    """Generate realistic mock data for testing and demos"""
    
    def __init__(self):
        self.analysis_engine = ConsumptionAnalysisEngine()
    
    def generate_meter_readings(
        self,
        property_id: str,
        user_id: str,
        meter_id: str,
        devices: List[Device],
        property_details: Property,
        days: int = 30,
        source: MeterReadingSource = MeterReadingSource.SIMULATED
    ) -> List[MeterReading]:
        """Generate realistic meter readings based on devices"""
        
        readings = []
        start_date = datetime.utcnow() - timedelta(days=days)
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Generate hourly readings for more realistic data
            for hour in range(24):
                timestamp = current_date + timedelta(hours=hour)
                
                # Calculate base consumption from all devices
                hourly_consumption = 0
                for device in devices:
                    if device.active:
                        hourly_consumption += self._calculate_hourly_device_consumption(
                            device, hour, current_date, property_details
                        )
                
                # Add base load (phantom loads, always-on devices)
                base_load = 0.15  # 150W base load
                hourly_consumption += base_load
                
                # Add some random variation (±10%)
                variation = random.uniform(0.9, 1.1)
                hourly_consumption *= variation
                
                # Calculate cost
                cost = self.analysis_engine._calculate_cost(hourly_consumption, property_details.tariff)
                
                reading = MeterReading(
                    property_id=property_id,
                    user_id=user_id,
                    meter_id=meter_id,
                    timestamp=timestamp,
                    consumption_kwh=round(hourly_consumption, 4),
                    production_kwh=0.0,  # No solar for now
                    cost_euros=round(cost, 4),
                    tariff_rate=self._get_tariff_rate_for_hour(hour, property_details.tariff),
                    source=source
                )
                readings.append(reading)
        
        return readings
    
    def _calculate_hourly_device_consumption(
        self,
        device: Device,
        hour: int,
        date: datetime,
        property_details: Property
    ) -> float:
        """Calculate device consumption for a specific hour"""
        
        # Usage patterns by device type and hour
        usage_probability = self._get_usage_probability(device, hour)
        
        if random.random() < usage_probability:
            # Device is running - use full wattage
            wattage = device.estimated_wattage
        else:
            # Device is in standby
            wattage = device.standby_wattage
        
        # Apply seasonal factors
        month = date.month
        seasonal_factor = 1.0
        if device.category.value in ['heating_cooling', 'water_heating']:
            seasonal_factor = self.analysis_engine.seasonal_factors.get(month, 1.0)
        
        # Convert to kWh for the hour
        hourly_kwh = (wattage * seasonal_factor) / 1000
        
        return hourly_kwh
    
    def _get_usage_probability(self, device: Device, hour: int) -> float:
        """Get probability that device is running at a given hour"""
        
        # Define usage patterns by device type
        patterns = {
            'refrigerator': 1.0,  # Always on
            'router': 1.0,  # Always on
            'tv': self._get_entertainment_pattern(hour),
            'pc': self._get_work_pattern(hour),
            'laptop': self._get_work_pattern(hour),
            'gaming_console': self._get_entertainment_pattern(hour),
            'washing_machine': self._get_appliance_pattern(hour),
            'dishwasher': self._get_evening_pattern(hour),
            'ev_charger': self._get_charging_pattern(hour),
            'led_lights': self._get_lighting_pattern(hour),
            'smart_bulbs': self._get_lighting_pattern(hour),
            'heat_pump': self._get_heating_pattern(hour),
            'water_heater': self._get_water_heating_pattern(hour),
        }
        
        device_type = device.device_type.value
        base_probability = patterns.get(device_type, 0.1)
        
        # Adjust based on runtime hours
        if device.daily_runtime_hours > 0:
            runtime_factor = device.daily_runtime_hours / 24
            base_probability = min(1.0, base_probability * runtime_factor * 2)
        
        return base_probability
    
    def _get_entertainment_pattern(self, hour: int) -> float:
        """TV, gaming console usage pattern"""
        if 7 <= hour <= 9:  # Morning
            return 0.3
        elif 18 <= hour <= 23:  # Evening
            return 0.8
        elif 12 <= hour <= 14:  # Lunch
            return 0.4
        else:
            return 0.1
    
    def _get_work_pattern(self, hour: int) -> float:
        """PC, laptop usage pattern"""
        if 8 <= hour <= 18:  # Work hours
            return 0.7
        elif 19 <= hour <= 22:  # Evening work
            return 0.4
        else:
            return 0.1
    
    def _get_appliance_pattern(self, hour: int) -> float:
        """Washing machine, dishwasher pattern"""
        if 10 <= hour <= 16:  # Daytime
            return 0.3
        elif 19 <= hour <= 21:  # Evening
            return 0.5
        else:
            return 0.05
    
    def _get_evening_pattern(self, hour: int) -> float:
        """Dishwasher pattern"""
        if 19 <= hour <= 22:  # After dinner
            return 0.6
        else:
            return 0.05
    
    def _get_charging_pattern(self, hour: int) -> float:
        """EV charging pattern"""
        if 22 <= hour <= 23 or 0 <= hour <= 6:  # Night charging
            return 0.8
        else:
            return 0.1
    
    def _get_lighting_pattern(self, hour: int) -> float:
        """Lighting usage pattern"""
        if 6 <= hour <= 8:  # Morning
            return 0.8
        elif 17 <= hour <= 23:  # Evening
            return 0.9
        else:
            return 0.1
    
    def _get_heating_pattern(self, hour: int) -> float:
        """Heating/cooling pattern"""
        if 6 <= hour <= 9:  # Morning warmup
            return 0.7
        elif 17 <= hour <= 22:  # Evening comfort
            return 0.8
        elif 1 <= hour <= 5:  # Night heating
            return 0.3
        else:
            return 0.2
    
    def _get_water_heating_pattern(self, hour: int) -> float:
        """Water heater pattern"""
        if 6 <= hour <= 9:  # Morning showers
            return 0.8
        elif 18 <= hour <= 21:  # Evening showers/dishes
            return 0.6
        else:
            return 0.2
    
    def _get_tariff_rate_for_hour(self, hour: int, tariff: ElectricityTariff) -> float:
        """Get tariff rate for specific hour"""
        if tariff.tariff_type == TariffType.DUAL:
            # Day rate: 7-22, Night rate: 22-7
            if 7 <= hour < 22:
                return tariff.day_rate or 0.28
            else:
                return tariff.night_rate or 0.20
        elif tariff.tariff_type == TariffType.DYNAMIC:
            # Simulate dynamic pricing with higher rates during peak hours
            if 17 <= hour <= 20:  # Peak hours
                return (tariff.single_rate or 0.24) * 1.5
            elif 11 <= hour <= 16:  # Mid-peak
                return (tariff.single_rate or 0.24) * 1.2
            else:  # Off-peak
                return (tariff.single_rate or 0.24) * 0.8
        else:
            return tariff.single_rate or 0.25