import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
  RefreshControl,
  Modal,
  TextInput,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

const { width } = Dimensions.get('window');
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// Types for Property Management
interface Property {
  id: string;
  name: string;
  property_type: 'home' | 'office' | 'rental' | 'vacation' | 'other';
  address: string;
  city: string;
  postal_code: string;
  region: 'brussels' | 'flanders' | 'wallonia';
  square_meters?: number;
  occupants?: number;
  meter_id?: string;
  created_at: string;
  active: boolean;
}

interface Device {
  id: string;
  property_id: string;
  name: string;
  device_type: string;
  category: string;
  estimated_wattage: number;
  daily_runtime_hours: number;
  brand?: string;
  model?: string;
  smart_integration_id?: string;
  created_at: string;
  active: boolean;
}

interface DeviceTemplate {
  device_type: string;
  category: string;
  name: string;
  typical_wattage: number;
  typical_daily_hours: number;
  typical_weekly_hours: number;
  standby_wattage: number;
}

interface UsageScenario {
  name: string;
  description: string;
  typical_monthly_kwh: number;
  typical_monthly_cost: number;
  device_count: number;
}

export default function Properties() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceTemplates, setDeviceTemplates] = useState<DeviceTemplate[]>([]);
  const [usageScenarios, setUsageScenarios] = useState<Record<string, UsageScenario>>({});
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>('');
  
  // Modal states
  const [showPropertyModal, setShowPropertyModal] = useState(false);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [showDeviceTemplates, setShowDeviceTemplates] = useState(false);
  
  // Form states
  const [propertyForm, setPropertyForm] = useState({
    name: '',
    property_type: 'home',
    address: '',
    city: '',
    postal_code: '',
    region: 'brussels',
    square_meters: '',
    occupants: '',
  });
  
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    device_type: '',
    category: '',
    estimated_wattage: '',
    daily_runtime_hours: '',
    brand: '',
    model: '',
  });

  useFocusEffect(
    useCallback(() => {
      loadInitialData();
    }, [])
  );

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      // Load properties, device templates, and scenarios in parallel
      await Promise.all([
        loadProperties(),
        loadDeviceTemplates(),
        loadUsageScenarios(),
      ]);
    } catch (error) {
      console.error('Error loading initial data:', error);
      setError('Failed to load property data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/properties`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProperties(data);
        
        // Auto-select first property if available
        if (data.length > 0 && !selectedProperty) {
          setSelectedProperty(data[0]);
          loadPropertyDevices(data[0].id);
        }
      } else if (response.status === 401) {
        router.replace('/');
      }
    } catch (error) {
      console.error('Error loading properties:', error);
    }
  };

  const loadPropertyDevices = async (propertyId: string) => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/properties/${propertyId}/devices`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  const loadDeviceTemplates = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/device-templates`);
      if (response.ok) {
        const data = await response.json();
        setDeviceTemplates(data.common_devices || []);
      }
    } catch (error) {
      console.error('Error loading device templates:', error);
    }
  };

  const loadUsageScenarios = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/usage-scenarios`);
      if (response.ok) {
        const data = await response.json();
        setUsageScenarios(data.scenarios || {});
      }
    } catch (error) {
      console.error('Error loading usage scenarios:', error);
    }
  };

  const setupScenario = async (scenarioKey: string) => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/setup-scenario/${scenarioKey}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert(
          'Success!',
          `${data.message}\n\nCreated ${data.devices_created} devices with ${data.meter_readings_created} meter readings.`,
          [{ text: 'OK', onPress: () => loadProperties() }]
        );
        setShowScenarioModal(false);
      } else {
        Alert.alert('Error', 'Failed to set up scenario. Please try again.');
      }
    } catch (error) {
      console.error('Error setting up scenario:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const createPropertyFromTemplate = async (template: DeviceTemplate) => {
    const newDevice = {
      property_id: selectedProperty?.id || '',
      name: template.name,
      device_type: template.device_type,
      category: template.category,
      estimated_wattage: template.typical_wattage,
      daily_runtime_hours: template.typical_daily_hours,
      weekly_runtime_hours: template.typical_weekly_hours,
      brand: '',
      model: '',
    };

    await createDevice(newDevice);
  };

  const createDevice = async (deviceData: any) => {
    try {
      if (!selectedProperty) {
        Alert.alert('Error', 'Please select a property first');
        return;
      }

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/properties/${selectedProperty.id}/devices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (response.ok) {
        Alert.alert('Success', 'Device added successfully!');
        loadPropertyDevices(selectedProperty.id);
        setShowDeviceModal(false);
        setShowDeviceTemplates(false);
        resetDeviceForm();
      } else {
        Alert.alert('Error', 'Failed to add device. Please try again.');
      }
    } catch (error) {
      console.error('Error creating device:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    }
  };

  const createProperty = async () => {
    try {
      if (!propertyForm.name || !propertyForm.address || !propertyForm.city) {
        Alert.alert('Error', 'Please fill in all required fields (Name, Address, City)');
        return;
      }

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const propertyData = {
        name: propertyForm.name,
        property_type: propertyForm.property_type,
        address: propertyForm.address,
        city: propertyForm.city,
        postal_code: propertyForm.postal_code,
        region: propertyForm.region,
        square_meters: propertyForm.square_meters ? parseInt(propertyForm.square_meters) : undefined,
        occupants: propertyForm.occupants ? parseInt(propertyForm.occupants) : undefined,
        meter_id: `METER_${Date.now()}`,
        api_provider: null,
      };

      const response = await fetch(`${BACKEND_URL}/properties`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(propertyData),
      });

      if (response.ok) {
        Alert.alert('Success', 'Property created successfully!');
        setShowPropertyModal(false);
        resetPropertyForm();
        loadProperties();
      } else {
        Alert.alert('Error', 'Failed to create property. Please try again.');
      }
    } catch (error) {
      console.error('Error creating property:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    }
  };

  const resetPropertyForm = () => {
    setPropertyForm({
      name: '',
      property_type: 'home',
      address: '',
      city: '',
      postal_code: '',
      region: 'brussels',
      square_meters: '',
      occupants: '',
    });
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadInitialData();
    setRefreshing(false);
  };

  const getPropertyTypeIcon = (type: string) => {
    switch (type) {
      case 'home': return '🏠';
      case 'office': return '🏢';
      case 'rental': return '🏘️';
      case 'vacation': return '🏖️';
      default: return '🏠';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'major_appliances': return '🏠';
      case 'electronics': return '📱';
      case 'lighting': return '💡';
      case 'heating_cooling': return '🌡️';
      case 'water_heating': return '🚿';
      case 'ev_charging': return '🔌';
      default: return '⚡';
    }
  };

  const formatPowerConsumption = (wattage: number, hours: number) => {
    const dailyKwh = (wattage * hours) / 1000;
    const monthlyKwh = dailyKwh * 30;
    const estimatedCost = monthlyKwh * 0.25; // €0.25 per kWh average
    
    return {
      dailyKwh: dailyKwh.toFixed(2),
      monthlyKwh: monthlyKwh.toFixed(1),
      estimatedCost: estimatedCost.toFixed(2),
    };
  };

  if (loading && properties.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading properties...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🏠 Property Management</Text>
        <Text style={styles.subtitle}>Manage your properties and devices</Text>
        
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowScenarioModal(true)}
          >
            <Text style={styles.actionButtonText}>📋 Demo Scenarios</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowPropertyModal(true)}
          >
            <Text style={styles.actionButtonText}>+ Add Property</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Properties List */}
        {properties.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyStateTitle}>No Properties Yet</Text>
            <Text style={styles.emptyStateText}>
              Add your first property or try a demo scenario to get started with energy management.
            </Text>
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={() => setShowScenarioModal(true)}
            >
              <Text style={styles.primaryButtonText}>Try Demo Scenario</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <Text style={styles.sectionTitle}>Your Properties</Text>
            {properties.map((property) => (
              <TouchableOpacity
                key={property.id}
                style={[
                  styles.propertyCard,
                  selectedProperty?.id === property.id && styles.selectedPropertyCard
                ]}
                onPress={() => {
                  setSelectedProperty(property);
                  loadPropertyDevices(property.id);
                }}
              >
                <View style={styles.propertyHeader}>
                  <View style={styles.propertyTitleRow}>
                    <Text style={styles.propertyIcon}>
                      {getPropertyTypeIcon(property.property_type)}
                    </Text>
                    <View style={styles.propertyInfo}>
                      <Text style={styles.propertyName}>{property.name}</Text>
                      <Text style={styles.propertyDetails}>
                        {property.address}, {property.city}
                      </Text>
                      <Text style={styles.propertyMeta}>
                        {property.property_type} • {property.region}
                        {property.square_meters && ` • ${property.square_meters}m²`}
                        {property.occupants && ` • ${property.occupants} people`}
                      </Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            ))}

            {/* Selected Property Devices */}
            {selectedProperty && (
              <>
                <View style={styles.sectionHeader}>
                  <Text style={styles.sectionTitle}>
                    Devices in {selectedProperty.name}
                  </Text>
                  <TouchableOpacity
                    style={styles.addButton}
                    onPress={() => setShowDeviceTemplates(true)}
                  >
                    <Text style={styles.addButtonText}>+ Add Device</Text>
                  </TouchableOpacity>
                </View>

                {devices.length === 0 ? (
                  <View style={styles.emptyDevicesState}>
                    <Text style={styles.emptyStateText}>
                      No devices added yet. Add devices to track energy consumption.
                    </Text>
                  </View>
                ) : (
                  devices.map((device) => {
                    const consumption = formatPowerConsumption(
                      device.estimated_wattage,
                      device.daily_runtime_hours
                    );
                    
                    return (
                      <View key={device.id} style={styles.deviceCard}>
                        <View style={styles.deviceHeader}>
                          <Text style={styles.deviceIcon}>
                            {getCategoryIcon(device.category)}
                          </Text>
                          <View style={styles.deviceInfo}>
                            <Text style={styles.deviceName}>{device.name}</Text>
                            <Text style={styles.deviceDetails}>
                              {device.estimated_wattage}W • {device.daily_runtime_hours}h/day
                            </Text>
                            {device.brand && device.model && (
                              <Text style={styles.deviceMeta}>
                                {device.brand} {device.model}
                              </Text>
                            )}
                          </View>
                        </View>
                        
                        <View style={styles.consumptionInfo}>
                          <View style={styles.consumptionItem}>
                            <Text style={styles.consumptionValue}>
                              {consumption.dailyKwh} kWh
                            </Text>
                            <Text style={styles.consumptionLabel}>Daily</Text>
                          </View>
                          <View style={styles.consumptionItem}>
                            <Text style={styles.consumptionValue}>
                              {consumption.monthlyKwh} kWh
                            </Text>
                            <Text style={styles.consumptionLabel}>Monthly</Text>
                          </View>
                          <View style={styles.consumptionItem}>
                            <Text style={styles.consumptionValue}>
                              €{consumption.estimatedCost}
                            </Text>
                            <Text style={styles.consumptionLabel}>Est. Cost</Text>
                          </View>
                        </View>
                      </View>
                    );
                  })
                )}
              </>
            )}
          </>
        )}
      </ScrollView>

      {/* Usage Scenarios Modal */}
      <Modal
        visible={showScenarioModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Demo Scenarios</Text>
            <TouchableOpacity onPress={() => setShowScenarioModal(false)}>
              <Text style={styles.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalDescription}>
              Try these realistic scenarios to explore property and device management features:
            </Text>
            
            {Object.entries(usageScenarios).map(([key, scenario]) => (
              <TouchableOpacity
                key={key}
                style={styles.scenarioCard}
                onPress={() => setupScenario(key)}
              >
                <Text style={styles.scenarioName}>{scenario.name}</Text>
                <Text style={styles.scenarioDescription}>{scenario.description}</Text>
                <View style={styles.scenarioStats}>
                  <Text style={styles.scenarioStat}>
                    📱 {scenario.device_count} devices
                  </Text>
                  <Text style={styles.scenarioStat}>
                    ⚡ {scenario.typical_monthly_kwh} kWh/month
                  </Text>
                  <Text style={styles.scenarioStat}>
                    💰 €{scenario.typical_monthly_cost}/month
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Device Templates Modal */}
      <Modal
        visible={showDeviceTemplates}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Add Device</Text>
            <TouchableOpacity onPress={() => setShowDeviceTemplates(false)}>
              <Text style={styles.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalDescription}>
              Choose from common devices with pre-filled power consumption estimates:
            </Text>
            
            {deviceTemplates.map((template, index) => {
              const consumption = formatPowerConsumption(
                template.typical_wattage,
                template.typical_daily_hours
              );
              
              return (
                <TouchableOpacity
                  key={index}
                  style={styles.templateCard}
                  onPress={() => createPropertyFromTemplate(template)}
                >
                  <View style={styles.templateHeader}>
                    <Text style={styles.templateIcon}>
                      {getCategoryIcon(template.category)}
                    </Text>
                    <View style={styles.templateInfo}>
                      <Text style={styles.templateName}>{template.name}</Text>
                      <Text style={styles.templateDetails}>
                        {template.typical_wattage}W • {template.typical_daily_hours}h/day
                      </Text>
                    </View>
                  </View>
                  <View style={styles.templateConsumption}>
                    <Text style={styles.templateConsumptionText}>
                      ~{consumption.monthlyKwh} kWh/month • €{consumption.estimatedCost}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    color: '#fff',
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    padding: 20,
    paddingTop: 10,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    color: '#999',
    fontSize: 16,
    marginBottom: 16,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    flex: 1,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    marginTop: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 12,
  },
  addButton: {
    backgroundColor: '#333',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  addButtonText: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
    marginTop: 60,
  },
  emptyStateTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  emptyStateText: {
    color: '#999',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  emptyDevicesState: {
    padding: 20,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  propertyCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  selectedPropertyCard: {
    borderColor: '#4CAF50',
    backgroundColor: '#1B2A1B',
  },
  propertyHeader: {
    marginBottom: 8,
  },
  propertyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  propertyIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  propertyInfo: {
    flex: 1,
  },
  propertyName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  propertyDetails: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 2,
  },
  propertyMeta: {
    color: '#999',
    fontSize: 12,
  },
  deviceCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  deviceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  deviceIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    color: '#fff',
    fontSize: 15,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  deviceDetails: {
    color: '#ccc',
    fontSize: 13,
    marginBottom: 2,
  },
  deviceMeta: {
    color: '#999',
    fontSize: 12,
  },
  consumptionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  consumptionItem: {
    alignItems: 'center',
    flex: 1,
  },
  consumptionValue: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  consumptionLabel: {
    color: '#999',
    fontSize: 11,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  modalCloseText: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalDescription: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 20,
  },
  scenarioCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  scenarioName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  scenarioDescription: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  scenarioStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  scenarioStat: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
  },
  templateCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  templateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  templateIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  templateInfo: {
    flex: 1,
  },
  templateName: {
    color: '#fff',
    fontSize: 15,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  templateDetails: {
    color: '#ccc',
    fontSize: 13,
  },
  templateConsumption: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  templateConsumptionText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
  },
});