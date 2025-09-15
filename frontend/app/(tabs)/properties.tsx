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
  Switch,
  KeyboardAvoidingView,
  Platform,
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
  weekly_runtime_hours: number;
  standby_wattage: number;
  brand?: string;
  model?: string;
  energy_rating?: string;
  smart_integration_id?: string;
  notes?: string;
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

interface DeviceEstimate {
  device_id: string;
  device_name: string;
  estimated_daily_kwh: number;
  estimated_weekly_kwh: number;
  estimated_monthly_kwh: number;
  estimated_daily_cost: number;
  estimated_weekly_cost: number;
  estimated_monthly_cost: number;
  confidence_score: number;
}

interface PropertyDetails {
  property: Property;
  devices: Device[];
  device_estimates: DeviceEstimate[];
  recent_readings: any[];
  alerts: any[];
  discrepancies: any[];
  summary: {
    total_devices: number;
    total_readings: number;
    has_mock_data: boolean;
  };
}

export default function Properties() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [propertyDetails, setPropertyDetails] = useState<PropertyDetails | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceTemplates, setDeviceTemplates] = useState<DeviceTemplate[]>([]);
  const [usageScenarios, setUsageScenarios] = useState<Record<string, UsageScenario>>({});
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  
  // Modal states
  const [showPropertyModal, setShowPropertyModal] = useState(false);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [showDeviceTemplates, setShowDeviceTemplates] = useState(false);
  const [showCSVUploadModal, setShowCSVUploadModal] = useState(false);
  
  // View states
  const [currentView, setCurrentView] = useState<'list' | 'details' | 'devices'>('list');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  
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
    meter_id: '',
  });
  
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    device_type: '',
    category: '',
    estimated_wattage: '',
    daily_runtime_hours: '',
    weekly_runtime_hours: '',
    standby_wattage: '0',
    brand: '',
    model: '',
    energy_rating: '',
    smart_integration_id: '',
    notes: '',
  });
  
  const [csvForm, setCsvForm] = useState({
    csv_content: '',
    data_format: 'hourly',
  });

  // Load data on component focus
  useFocusEffect(
    useCallback(() => {
      loadPropertiesData();
    }, [])
  );

  const loadPropertiesData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      // Load properties, device templates, and scenarios in parallel
      const [propertiesResponse, templatesResponse, scenariosResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/properties`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${BACKEND_URL}/api/device-templates`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${BACKEND_URL}/api/usage-scenarios`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      ]);

      if (propertiesResponse.status === 401) {
        await AsyncStorage.multiRemove(['energo_token', 'energo_user']);
        router.replace('/');
        return;
      }

      const [propertiesData, templatesData, scenariosData] = await Promise.all([
        propertiesResponse.json(),
        templatesResponse.json(),
        scenariosResponse.json()
      ]);

      if (propertiesResponse.ok) {
        setProperties(propertiesData.properties || []);
      }

      if (templatesResponse.ok && templatesData.common_devices) {
        setDeviceTemplates(templatesData.common_devices);
      }

      if (scenariosResponse.ok && scenariosData.scenarios) {
        setUsageScenarios(scenariosData.scenarios);
      }

    } catch (error) {
      console.error('Error loading properties data:', error);
      setError('Failed to load properties data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadPropertyDetails = async (property: Property) => {
    try {
      setDetailsLoading(true);
      setSelectedProperty(property);
      setCurrentView('details');
      
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/properties/${property.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPropertyDetails(data);
        setDevices(data.devices || []);
      } else {
        throw new Error('Failed to load property details');
      }
    } catch (error) {
      console.error('Error loading property details:', error);
      Alert.alert('Error', 'Failed to load property details');
    } finally {
      setDetailsLoading(false);
    }
  };

  const createProperty = async () => {
    try {
      if (!propertyForm.name.trim() || !propertyForm.address.trim()) {
        Alert.alert('Error', 'Please fill in all required fields');
        return;
      }

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/properties`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...propertyForm,
          square_meters: propertyForm.square_meters ? parseInt(propertyForm.square_meters) : null,
          occupants: propertyForm.occupants ? parseInt(propertyForm.occupants) : null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Success', 'Property created successfully');
        setShowPropertyModal(false);
        resetPropertyForm();
        loadPropertiesData();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create property');
      }
    } catch (error) {
      console.error('Error creating property:', error);
      Alert.alert('Error', error.message || 'Failed to create property');
    }
  };

  const setupPropertyScenario = async (scenarioKey: string) => {
    try {
      if (!selectedProperty) return;

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/properties/${selectedProperty.id}/setup-scenario`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario: scenarioKey,
          generate_mock_data: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Success', data.message);
        setShowScenarioModal(false);
        loadPropertyDetails(selectedProperty);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to setup scenario');
      }
    } catch (error) {
      console.error('Error setting up scenario:', error);
      Alert.alert('Error', error.message || 'Failed to setup scenario');
    }
  };

  const addDeviceFromTemplate = async (template: DeviceTemplate) => {
    try {
      if (!selectedProperty) return;

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const deviceData = {
        name: template.name,
        device_type: template.device_type,
        category: template.category,
        estimated_wattage: template.typical_wattage,
        daily_runtime_hours: template.typical_daily_hours,
        weekly_runtime_hours: template.typical_weekly_hours,
        standby_wattage: template.standby_wattage,
      };

      const response = await fetch(`${BACKEND_URL}/api/properties/${selectedProperty.id}/devices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (response.ok) {
        Alert.alert('Success', 'Device added successfully');
        setShowDeviceTemplates(false);
        loadPropertyDetails(selectedProperty);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add device');
      }
    } catch (error) {
      console.error('Error adding device:', error);
      Alert.alert('Error', error.message || 'Failed to add device');
    }
  };

  const addCustomDevice = async () => {
    try {
      if (!selectedProperty || !deviceForm.name.trim() || !deviceForm.estimated_wattage) {
        Alert.alert('Error', 'Please fill in all required fields');
        return;
      }

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const deviceData = {
        ...deviceForm,
        estimated_wattage: parseInt(deviceForm.estimated_wattage),
        daily_runtime_hours: parseFloat(deviceForm.daily_runtime_hours) || 0,
        weekly_runtime_hours: parseFloat(deviceForm.weekly_runtime_hours) || 0,
        standby_wattage: parseInt(deviceForm.standby_wattage) || 0,
      };

      const response = await fetch(`${BACKEND_URL}/api/properties/${selectedProperty.id}/devices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (response.ok) {
        Alert.alert('Success', 'Device added successfully');
        setShowDeviceModal(false);
        resetDeviceForm();
        loadPropertyDetails(selectedProperty);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add device');
      }
    } catch (error) {
      console.error('Error adding device:', error);
      Alert.alert('Error', error.message || 'Failed to add device');
    }
  };

  const uploadCSVData = async () => {
    try {
      if (!selectedProperty || !csvForm.csv_content.trim()) {
        Alert.alert('Error', 'Please provide CSV content');
        return;
      }

      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/properties/${selectedProperty.id}/upload-csv`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(csvForm),
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Success', `${data.readings_imported} readings imported successfully`);
        setShowCSVUploadModal(false);
        setCsvForm({ csv_content: '', data_format: 'hourly' });
        loadPropertyDetails(selectedProperty);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload CSV');
      }
    } catch (error) {
      console.error('Error uploading CSV:', error);
      Alert.alert('Error', error.message || 'Failed to upload CSV');
    }
  };

  const deleteDevice = async (device: Device) => {
    Alert.alert(
      'Delete Device',
      `Are you sure you want to delete "${device.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const token = await AsyncStorage.getItem('energo_token');
              if (!token || !selectedProperty) return;

              const response = await fetch(`${BACKEND_URL}/api/properties/${selectedProperty.id}/devices/${device.id}`, {
                method: 'DELETE',
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
              });

              if (response.ok) {
                Alert.alert('Success', 'Device deleted successfully');
                loadPropertyDetails(selectedProperty);
              } else {
                throw new Error('Failed to delete device');
              }
            } catch (error) {
              console.error('Error deleting device:', error);
              Alert.alert('Error', 'Failed to delete device');
            }
          }
        }
      ]
    );
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
      meter_id: '',
    });
  };

  const resetDeviceForm = () => {
    setDeviceForm({
      name: '',
      device_type: '',
      category: '',
      estimated_wattage: '',
      daily_runtime_hours: '',
      weekly_runtime_hours: '',
      standby_wattage: '0',
      brand: '',
      model: '',
      energy_rating: '',
      smart_integration_id: '',
      notes: '',
    });
  };

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadPropertiesData().finally(() => setRefreshing(false));
  }, []);

  const renderPropertyCard = ({ item }: { item: Property }) => (
    <TouchableOpacity
      style={styles.propertyCard}
      onPress={() => loadPropertyDetails(item)}
    >
      <LinearGradient
        colors={['#1a1a1a', '#2a2a2a']}
        style={styles.propertyCardGradient}
      >
        <View style={styles.propertyHeader}>
          <Text style={styles.propertyName}>{item.name}</Text>
          <Text style={styles.propertyType}>{item.property_type.toUpperCase()}</Text>
        </View>
        <Text style={styles.propertyAddress}>{item.address}</Text>
        <Text style={styles.propertyLocation}>{item.city}, {item.region.toUpperCase()}</Text>
        {item.square_meters && (
          <Text style={styles.propertyDetails}>{item.square_meters}m² • {item.occupants || 1} occupants</Text>
        )}
      </LinearGradient>
    </TouchableOpacity>
  );

  const renderDeviceCard = ({ item }: { item: Device }) => {
    const estimate = propertyDetails?.device_estimates.find(e => e.device_id === item.id);
    
    return (
      <View style={styles.deviceCard}>
        <View style={styles.deviceHeader}>
          <Text style={styles.deviceName}>{item.name}</Text>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => deleteDevice(item)}
          >
            <Text style={styles.deleteButtonText}>×</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.deviceType}>{item.category.replace('_', ' ')} • {item.estimated_wattage}W</Text>
        <Text style={styles.deviceRuntime}>
          {item.daily_runtime_hours}h/day • {item.weekly_runtime_hours}h/week
        </Text>
        {estimate && (
          <View style={styles.deviceEstimate}>
            <Text style={styles.estimateText}>
              Est: {estimate.estimated_daily_kwh.toFixed(2)} kWh/day • €{estimate.estimated_daily_cost.toFixed(2)}/day
            </Text>
            <Text style={styles.confidenceText}>
              Confidence: {(estimate.confidence_score * 100).toFixed(0)}%
            </Text>
          </View>
        )}
        {item.smart_integration_id && (
          <Text style={styles.smartIntegration}>📱 Smart: {item.smart_integration_id}</Text>
        )}
      </View>
    );
  };

  const renderDeviceTemplate = ({ item }: { item: DeviceTemplate }) => (
    <TouchableOpacity
      style={styles.templateCard}
      onPress={() => addDeviceFromTemplate(item)}
    >
      <Text style={styles.templateName}>{item.name}</Text>
      <Text style={styles.templateDetails}>
        {item.typical_wattage}W • {item.typical_daily_hours}h/day
      </Text>
      <Text style={styles.templateCategory}>{item.category.replace('_', ' ')}</Text>
    </TouchableOpacity>
  );

  const renderScenarioOption = (scenarioKey: string, scenario: UsageScenario) => (
    <TouchableOpacity
      key={scenarioKey}
      style={styles.scenarioCard}
      onPress={() => setupPropertyScenario(scenarioKey)}
    >
      <Text style={styles.scenarioName}>{scenario.name}</Text>
      <Text style={styles.scenarioDescription}>{scenario.description}</Text>
      <Text style={styles.scenarioStats}>
        {scenario.device_count} devices • {scenario.typical_monthly_kwh} kWh/month • €{scenario.typical_monthly_cost}/month
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading properties...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Properties List View
  if (currentView === 'list') {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Properties</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowPropertyModal(true)}
          >
            <Text style={styles.addButtonText}>+ Add Property</Text>
          </TouchableOpacity>
        </View>

        {error ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={loadPropertiesData}>
              <Text style={styles.retryButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <FlatList
            data={properties}
            renderItem={renderPropertyCard}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.propertiesList}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No properties yet</Text>
                <Text style={styles.emptySubtext}>Add your first property to get started</Text>
              </View>
            }
          />
        )}

        {/* Property Creation Modal */}
        <Modal
          visible={showPropertyModal}
          animationType="slide"
          presentationStyle="formSheet"
        >
          <SafeAreaView style={styles.modalContainer}>
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={styles.modalKeyboardView}
            >
              <ScrollView style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Add New Property</Text>
                  <TouchableOpacity
                    style={styles.modalCloseButton}
                    onPress={() => {
                      setShowPropertyModal(false);
                      resetPropertyForm();
                    }}
                  >
                    <Text style={styles.modalCloseText}>×</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Property Name *</Text>
                  <TextInput
                    style={styles.formInput}
                    value={propertyForm.name}
                    onChangeText={(text) => setPropertyForm({ ...propertyForm, name: text })}
                    placeholder="e.g., My Home, Office"
                    placeholderTextColor="#666"
                  />
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Property Type</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.typeSelector}>
                      {['home', 'office', 'rental', 'vacation', 'other'].map((type) => (
                        <TouchableOpacity
                          key={type}
                          style={[
                            styles.typeOption,
                            propertyForm.property_type === type && styles.typeOptionSelected
                          ]}
                          onPress={() => setPropertyForm({ ...propertyForm, property_type: type })}
                        >
                          <Text
                            style={[
                              styles.typeOptionText,
                              propertyForm.property_type === type && styles.typeOptionTextSelected
                            ]}
                          >
                            {type.charAt(0).toUpperCase() + type.slice(1)}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Address *</Text>
                  <TextInput
                    style={styles.formInput}
                    value={propertyForm.address}
                    onChangeText={(text) => setPropertyForm({ ...propertyForm, address: text })}
                    placeholder="Street address"
                    placeholderTextColor="#666"
                  />
                </View>

                <View style={styles.formRow}>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>City</Text>
                    <TextInput
                      style={styles.formInput}
                      value={propertyForm.city}
                      onChangeText={(text) => setPropertyForm({ ...propertyForm, city: text })}
                      placeholder="City"
                      placeholderTextColor="#666"
                    />
                  </View>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Postal Code</Text>
                    <TextInput
                      style={styles.formInput}
                      value={propertyForm.postal_code}
                      onChangeText={(text) => setPropertyForm({ ...propertyForm, postal_code: text })}
                      placeholder="1000"
                      placeholderTextColor="#666"
                    />
                  </View>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Region</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.typeSelector}>
                      {['brussels', 'flanders', 'wallonia'].map((region) => (
                        <TouchableOpacity
                          key={region}
                          style={[
                            styles.typeOption,
                            propertyForm.region === region && styles.typeOptionSelected
                          ]}
                          onPress={() => setPropertyForm({ ...propertyForm, region: region })}
                        >
                          <Text
                            style={[
                              styles.typeOptionText,
                              propertyForm.region === region && styles.typeOptionTextSelected
                            ]}
                          >
                            {region.charAt(0).toUpperCase() + region.slice(1)}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                <View style={styles.formRow}>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Size (m²)</Text>
                    <TextInput
                      style={styles.formInput}
                      value={propertyForm.square_meters}
                      onChangeText={(text) => setPropertyForm({ ...propertyForm, square_meters: text })}
                      placeholder="150"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Occupants</Text>
                    <TextInput
                      style={styles.formInput}
                      value={propertyForm.occupants}
                      onChangeText={(text) => setPropertyForm({ ...propertyForm, occupants: text })}
                      placeholder="4"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Smart Meter ID (Optional)</Text>
                  <TextInput
                    style={styles.formInput}
                    value={propertyForm.meter_id}
                    onChangeText={(text) => setPropertyForm({ ...propertyForm, meter_id: text })}
                    placeholder="e.g., BE_123456789"
                    placeholderTextColor="#666"
                  />
                </View>

                <TouchableOpacity
                  style={styles.createButton}
                  onPress={createProperty}
                >
                  <Text style={styles.createButtonText}>Create Property</Text>
                </TouchableOpacity>
              </ScrollView>
            </KeyboardAvoidingView>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    );
  }

  // Property Details View
  if (currentView === 'details' && selectedProperty) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setCurrentView('list')}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{selectedProperty.name}</Text>
        </View>

        {detailsLoading ? (
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color="#4CAF50" />
            <Text style={styles.loadingText}>Loading property details...</Text>
          </View>
        ) : (
          <ScrollView style={styles.detailsContainer}>
            {/* Property Info */}
            <View style={styles.infoCard}>
              <Text style={styles.cardTitle}>Property Information</Text>
              <Text style={styles.infoText}>📍 {selectedProperty.address}</Text>
              <Text style={styles.infoText">🏙️ {selectedProperty.city}, {selectedProperty.region.toUpperCase()}</Text>
              {selectedProperty.square_meters && (
                <Text style={styles.infoText}>📐 {selectedProperty.square_meters}m² • {selectedProperty.occupants || 1} occupants</Text>
              )}
              {selectedProperty.meter_id && (
                <Text style={styles.infoText}>⚡ Meter: {selectedProperty.meter_id}</Text>
              )}
            </View>

            {/* Summary Statistics */}
            {propertyDetails && (
              <View style={styles.summaryCard}>
                <Text style={styles.cardTitle}>Summary</Text>
                <View style={styles.summaryRow}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryNumber}>{propertyDetails.summary.total_devices}</Text>
                    <Text style={styles.summaryLabel}>Devices</Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryNumber}>{propertyDetails.summary.total_readings}</Text>
                    <Text style={styles.summaryLabel}>Readings</Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryNumber}>
                      {propertyDetails.device_estimates.reduce((sum, est) => sum + est.estimated_monthly_kwh, 0).toFixed(0)}
                    </Text>
                    <Text style={styles.summaryLabel}>kWh/month</Text>
                  </View>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryNumber}>
                      €{propertyDetails.device_estimates.reduce((sum, est) => sum + est.estimated_monthly_cost, 0).toFixed(0)}
                    </Text>
                    <Text style={styles.summaryLabel}>Cost/month</Text>
                  </View>
                </View>
              </View>
            )}

            {/* Alerts */}
            {propertyDetails?.alerts && propertyDetails.alerts.length > 0 && (
              <View style={styles.alertsCard}>
                <Text style={styles.cardTitle}>⚠️ Alerts</Text>
                {propertyDetails.alerts.map((alert, index) => (
                  <View key={index} style={styles.alertItem}>
                    <Text style={styles.alertTitle}>{alert.title}</Text>
                    <Text style={styles.alertMessage}>{alert.message}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => setCurrentView('devices')}
              >
                <Text style={styles.actionButtonText}>📱 Manage Devices</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => setShowScenarioModal(true)}
              >
                <Text style={styles.actionButtonText}>🎭 Load Scenario</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => setShowCSVUploadModal(true)}
              >
                <Text style={styles.actionButtonText}>📊 Upload CSV Data</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        )}

        {/* Scenario Selection Modal */}
        <Modal
          visible={showScenarioModal}
          animationType="slide"
          presentationStyle="formSheet"
        >
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choose Usage Scenario</Text>
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowScenarioModal(false)}
              >
                <Text style={styles.modalCloseText}>×</Text>
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.modalContent}>
              {Object.entries(usageScenarios).map(([key, scenario]) =>
                renderScenarioOption(key, scenario)
              )}
            </ScrollView>
          </SafeAreaView>
        </Modal>

        {/* CSV Upload Modal */}
        <Modal
          visible={showCSVUploadModal}
          animationType="slide"
          presentationStyle="formSheet"
        >
          <SafeAreaView style={styles.modalContainer}>
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={styles.modalKeyboardView}
            >
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Upload CSV Meter Data</Text>
                <TouchableOpacity
                  style={styles.modalCloseButton}
                  onPress={() => setShowCSVUploadModal(false)}
                >
                  <Text style={styles.modalCloseText}>×</Text>
                </TouchableOpacity>
              </View>
              <ScrollView style={styles.modalContent}>
                <Text style={styles.formLabel}>CSV Format Instructions:</Text>
                <Text style={styles.instructionText}>
                  Expected columns: timestamp, consumption_kwh, production_kwh (optional)
                  {'\n'}Example:{'\n'}2024-01-01 00:00:00,1.5,0.0{'\n'}2024-01-01 01:00:00,1.2,0.0
                </Text>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Data Format</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.typeSelector}>
                      {['hourly', 'daily', 'monthly'].map((format) => (
                        <TouchableOpacity
                          key={format}
                          style={[
                            styles.typeOption,
                            csvForm.data_format === format && styles.typeOptionSelected
                          ]}
                          onPress={() => setCsvForm({ ...csvForm, data_format: format })}
                        >
                          <Text
                            style={[
                              styles.typeOptionText,
                              csvForm.data_format === format && styles.typeOptionTextSelected
                            ]}
                          >
                            {format.charAt(0).toUpperCase() + format.slice(1)}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>CSV Content</Text>
                  <TextInput
                    style={[styles.formInput, styles.textArea]}
                    value={csvForm.csv_content}
                    onChangeText={(text) => setCsvForm({ ...csvForm, csv_content: text })}
                    placeholder="Paste your CSV content here..."
                    placeholderTextColor="#666"
                    multiline
                    numberOfLines={10}
                  />
                </View>

                <TouchableOpacity
                  style={styles.createButton}
                  onPress={uploadCSVData}
                >
                  <Text style={styles.createButtonText}>Upload CSV Data</Text>
                </TouchableOpacity>
              </ScrollView>
            </KeyboardAvoidingView>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    );
  }

  // Device Management View
  if (currentView === 'devices' && selectedProperty) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setCurrentView('details')}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Devices</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowDeviceTemplates(true)}
          >
            <Text style={styles.addButtonText}>+ Add Device</Text>
          </TouchableOpacity>
        </View>

        <FlatList
          data={devices}
          renderItem={renderDeviceCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.devicesList}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No devices yet</Text>
              <Text style={styles.emptySubtext}>Add devices to track their energy consumption</Text>
            </View>
          }
        />

        {/* Device Templates Modal */}
        <Modal
          visible={showDeviceTemplates}
          animationType="slide"
          presentationStyle="formSheet"
        >
          <SafeAreaView style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Device</Text>
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setShowDeviceTemplates(false)}
              >
                <Text style={styles.modalCloseText}>×</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.templateTabs}>
              <TouchableOpacity
                style={styles.templateTab}
                onPress={() => setShowDeviceModal(true)}
              >
                <Text style={styles.templateTabText}>Custom Device</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.sectionTitle}>Quick Add - Common Devices</Text>
            <FlatList
              data={deviceTemplates}
              renderItem={renderDeviceTemplate}
              keyExtractor={(item) => item.device_type}
              contentContainerStyle={styles.templatesList}
              numColumns={2}
            />
          </SafeAreaView>
        </Modal>

        {/* Custom Device Modal */}
        <Modal
          visible={showDeviceModal}
          animationType="slide"
          presentationStyle="formSheet"
        >
          <SafeAreaView style={styles.modalContainer}>
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={styles.modalKeyboardView}
            >
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Add Custom Device</Text>
                <TouchableOpacity
                  style={styles.modalCloseButton}
                  onPress={() => {
                    setShowDeviceModal(false);
                    resetDeviceForm();
                  }}
                >
                  <Text style={styles.modalCloseText}>×</Text>
                </TouchableOpacity>
              </View>
              
              <ScrollView style={styles.modalContent}>
                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Device Name *</Text>
                  <TextInput
                    style={styles.formInput}
                    value={deviceForm.name}
                    onChangeText={(text) => setDeviceForm({ ...deviceForm, name: text })}
                    placeholder="e.g., Kitchen Fridge, Living Room TV"
                    placeholderTextColor="#666"
                  />
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Category</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.typeSelector}>
                      {['major_appliances', 'electronics', 'lighting', 'heating_cooling', 'ev_charging'].map((category) => (
                        <TouchableOpacity
                          key={category}
                          style={[
                            styles.typeOption,
                            deviceForm.category === category && styles.typeOptionSelected
                          ]}
                          onPress={() => setDeviceForm({ ...deviceForm, category: category })}
                        >
                          <Text
                            style={[
                              styles.typeOptionText,
                              deviceForm.category === category && styles.typeOptionTextSelected
                            ]}
                          >
                            {category.replace('_', ' ')}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                <View style={styles.formRow}>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Power (W) *</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.estimated_wattage}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, estimated_wattage: text })}
                      placeholder="150"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Standby (W)</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.standby_wattage}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, standby_wattage: text })}
                      placeholder="5"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                </View>

                <View style={styles.formRow}>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Daily Hours</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.daily_runtime_hours}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, daily_runtime_hours: text })}
                      placeholder="8"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Weekly Hours</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.weekly_runtime_hours}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, weekly_runtime_hours: text })}
                      placeholder="50"
                      placeholderTextColor="#666"
                      keyboardType="numeric"
                    />
                  </View>
                </View>

                <View style={styles.formRow}>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Brand</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.brand}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, brand: text })}
                      placeholder="Samsung"
                      placeholderTextColor="#666"
                    />
                  </View>
                  <View style={styles.formGroupHalf}>
                    <Text style={styles.formLabel}>Model</Text>
                    <TextInput
                      style={styles.formInput}
                      value={deviceForm.model}
                      onChangeText={(text) => setDeviceForm({ ...deviceForm, model: text })}
                      placeholder="RF28R7351SG"
                      placeholderTextColor="#666"
                    />
                  </View>
                </View>

                <View style={styles.formGroup}>
                  <Text style={styles.formLabel}>Smart Integration ID</Text>
                  <TextInput
                    style={styles.formInput}
                    value={deviceForm.smart_integration_id}
                    onChangeText={(text) => setDeviceForm({ ...deviceForm, smart_integration_id: text })}
                    placeholder="smart_plug_01, channel_3"
                    placeholderTextColor="#666"
                  />
                </View>

                <TouchableOpacity
                  style={styles.createButton}
                  onPress={addCustomDevice}
                >
                  <Text style={styles.createButtonText}>Add Device</Text>
                </TouchableOpacity>
              </ScrollView>
            </KeyboardAvoidingView>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
    textAlign: 'center',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    color: '#4CAF50',
    fontSize: 16,
  },
  addButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  loadingText: {
    color: '#999',
    marginTop: 16,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  errorText: {
    color: '#FF5252',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  propertiesList: {
    padding: 20,
  },
  propertyCard: {
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  propertyCardGradient: {
    padding: 20,
  },
  propertyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  propertyName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  propertyType: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    fontSize: 12,
    color: '#fff',
    fontWeight: '600',
  },
  propertyAddress: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 4,
  },
  propertyLocation: {
    color: '#999',
    fontSize: 14,
    marginBottom: 8,
  },
  propertyDetails: {
    color: '#999',
    fontSize: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    color: '#999',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtext: {
    color: '#666',
    fontSize: 14,
    textAlign: 'center',
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  modalKeyboardView: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  modalCloseButton: {
    padding: 8,
  },
  modalCloseText: {
    color: '#999',
    fontSize: 24,
    fontWeight: 'bold',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  // Form styles
  formGroup: {
    marginBottom: 20,
  },
  formRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  formGroupHalf: {
    flex: 1,
  },
  formLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  formInput: {
    backgroundColor: '#1a1a1a',
    borderColor: '#333',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#fff',
    fontSize: 16,
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  typeOption: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#333',
  },
  typeOptionSelected: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  typeOptionText: {
    color: '#999',
    fontSize: 14,
    fontWeight: '600',
  },
  typeOptionTextSelected: {
    color: '#fff',
  },
  createButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Details view styles
  detailsContainer: {
    flex: 1,
    padding: 20,
  },
  infoCard: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
  },
  cardTitle: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  infoText: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 8,
  },
  summaryCard: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  summaryItem: {
    alignItems: 'center',
    flex: 1,
  },
  summaryNumber: {
    color: '#4CAF50',
    fontSize: 24,
    fontWeight: 'bold',
  },
  summaryLabel: {
    color: '#999',
    fontSize: 12,
    marginTop: 4,
  },
  alertsCard: {
    backgroundColor: '#2a1a1a',
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FF5252',
  },
  alertItem: {
    marginBottom: 12,
  },
  alertTitle: {
    color: '#FF5252',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  alertMessage: {
    color: '#ccc',
    fontSize: 14,
  },
  actionButtons: {
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  actionButtonText: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: '600',
  },
  // Device styles
  devicesList: {
    padding: 20,
  },
  deviceCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  deviceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  deviceName: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  deleteButton: {
    width: 24,
    height: 24,
    backgroundColor: '#FF5252',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deleteButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  deviceType: {
    color: '#4CAF50',
    fontSize: 14,
    marginBottom: 4,
  },
  deviceRuntime: {
    color: '#999',
    fontSize: 12,
    marginBottom: 8,
  },
  deviceEstimate: {
    backgroundColor: '#0f0f0f',
    padding: 8,
    borderRadius: 4,
    marginBottom: 8,
  },
  estimateText: {
    color: '#ccc',
    fontSize: 12,
    marginBottom: 2,
  },
  confidenceText: {
    color: '#999',
    fontSize: 10,
  },
  smartIntegration: {
    color: '#2196F3',
    fontSize: 12,
  },
  // Template styles
  templatesList: {
    padding: 20,
  },
  templateCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    margin: 4,
    flex: 1,
    maxWidth: (width - 60) / 2,
    borderWidth: 1,
    borderColor: '#333',
  },
  templateName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  templateDetails: {
    color: '#4CAF50',
    fontSize: 12,
    marginBottom: 4,
  },
  templateCategory: {
    color: '#999',
    fontSize: 10,
  },
  templateTabs: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  templateTab: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  templateTabText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 20,
    marginBottom: 8,
  },
  // Scenario styles
  scenarioCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  scenarioName: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  scenarioDescription: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 8,
  },
  scenarioStats: {
    color: '#999',
    fontSize: 12,
  },
  instructionText: {
    color: '#999',
    fontSize: 12,
    marginBottom: 16,
    lineHeight: 16,
  },
});