import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const { width } = Dimensions.get('window');
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface UserSettings {
  language: string;
  currency_unit: string;
  notifications_enabled: boolean;
  high_usage_alerts: boolean;
  weekly_summary: boolean;
  subscription_plan: string;
  region?: string;
}

interface SubscriptionPlan {
  name: string;
  price: number;
  features: string[];
  limitations: string[];
}

interface SubscriptionData {
  current_plan: string;
  plans: {
    free: SubscriptionPlan;
    premium: SubscriptionPlan;
  };
  stripe_integration: string;
}

export default function Settings() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    loadUserData();
    fetchSettings();
    fetchSubscriptionData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('energo_user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        router.replace('/');
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings);
      } else {
        Alert.alert('Error', 'Failed to load settings');
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    }
  };

  const fetchSubscriptionData = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptionData(data);
      }
    } catch (error) {
      console.error('Error fetching subscription data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (newSettings: UserSettings) => {
    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) return;

      const response = await fetch(`${BACKEND_URL}/api/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSettings),
      });

      if (response.ok) {
        setSettings(newSettings);
        Alert.alert('Success', 'Settings updated successfully');
      } else {
        Alert.alert('Error', 'Failed to update settings');
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            console.log('Logout process started');
            setSaving(true);
            
            try {
              // Call logout endpoint if available
              const token = await AsyncStorage.getItem('energo_token');
              console.log('Token found:', !!token);
              
              if (token && BACKEND_URL) {
                try {
                  console.log('Calling logout API:', `${BACKEND_URL}/api/auth/logout`);
                  const response = await fetch(`${BACKEND_URL}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${token}`,
                      'Content-Type': 'application/json',
                    },
                    timeout: 5000,
                  });
                  console.log('Logout API response:', response.status);
                } catch (error) {
                  console.log('Logout API call failed, continuing with local logout:', error);
                }
              }
              
              // Clear local storage
              console.log('Clearing local storage...');
              await AsyncStorage.multiRemove(['energo_token', 'energo_user']);
              console.log('Local storage cleared');
              
              // Navigate to login screen
              console.log('Navigating to login screen...');
              router.replace('/');
              
            } catch (error) {
              console.error('Logout error:', error);
              Alert.alert('Error', 'Logout failed. Please try again.');
              
              // Even if there's an error, still try to clear storage and navigate
              try {
                await AsyncStorage.multiRemove(['energo_token', 'energo_user']);
                router.replace('/');
              } catch (clearError) {
                console.error('Failed to clear storage:', clearError);
                Alert.alert('Error', 'Failed to clear session. Please restart the app.');
              }
            } finally {
              setSaving(false);
            }
          },
        },
      ]
    );
  };

  const handleUpgrade = () => {
    Alert.alert(
      'Premium Subscription',
      'Premium subscription includes advanced analytics, unlimited AI insights, and predictive forecasting for just €8/month.',
      [
        { text: 'Maybe Later', style: 'cancel' },
        {
          text: 'Upgrade Now',
          onPress: () => {
            Alert.alert('Coming Soon', 'Stripe integration will be available soon!');
          },
        },
      ]
    );
  };

  if (loading || !settings) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading settings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>⚙️ Settings</Text>
          <Text style={styles.subtitle}>Customize your Energo experience</Text>
        </View>

        {/* User Profile */}
        <LinearGradient colors={['#1a1a1a', '#2a2a2a']} style={styles.profileCard}>
          <View style={styles.profileInfo}>
            <View style={styles.avatarContainer}>
              <Text style={styles.avatarText}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Text>
            </View>
            <View style={styles.userDetails}>
              <Text style={styles.userName}>{user?.name || 'User'}</Text>
              <Text style={styles.userEmail}>{user?.email || ''}</Text>
              <View style={styles.planBadge}>
                <Text style={styles.planText}>
                  {subscriptionData?.current_plan?.toUpperCase() || 'FREE'} PLAN
                </Text>
              </View>
            </View>
          </View>
        </LinearGradient>

        {/* Subscription */}
        {subscriptionData && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>💳 Subscription</Text>
            
            <View style={styles.subscriptionContainer}>
              <View style={styles.currentPlanCard}>
                <Text style={styles.currentPlanTitle}>
                  Current Plan: {subscriptionData.plans[subscriptionData.current_plan as keyof typeof subscriptionData.plans].name}
                </Text>
                <Text style={styles.currentPlanPrice}>
                  €{subscriptionData.plans[subscriptionData.current_plan as keyof typeof subscriptionData.plans].price}/month
                </Text>
              </View>

              {subscriptionData.current_plan === 'free' && (
                <TouchableOpacity style={styles.upgradeButton} onPress={handleUpgrade}>
                  <LinearGradient colors={['#4CAF50', '#45a049']} style={styles.upgradeGradient}>
                    <Text style={styles.upgradeButtonText}>⭐ Upgrade to Premium</Text>
                    <Text style={styles.upgradeSubtext}>Unlock all features for €8/month</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}

              <View style={styles.planFeaturesContainer}>
                <Text style={styles.featuresTitle}>Current Features:</Text>
                {subscriptionData.plans[subscriptionData.current_plan as keyof typeof subscriptionData.plans].features.map((feature, index) => (
                  <Text key={index} style={styles.featureItem}>✅ {feature}</Text>
                ))}
                
                {subscriptionData.plans[subscriptionData.current_plan as keyof typeof subscriptionData.plans].limitations.length > 0 && (
                  <>
                    <Text style={styles.limitationsTitle}>Limitations:</Text>
                    {subscriptionData.plans[subscriptionData.current_plan as keyof typeof subscriptionData.plans].limitations.map((limitation, index) => (
                      <Text key={index} style={styles.limitationItem}>⚠️ {limitation}</Text>
                    ))}
                  </>
                )}
              </View>
            </View>
          </View>
        )}

        {/* Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🎛️ Preferences</Text>
          
          <View style={styles.settingCard}>
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Language</Text>
              <View style={styles.languageSelector}>
                {['en', 'fr', 'nl'].map((lang) => (
                  <TouchableOpacity
                    key={lang}
                    style={[
                      styles.languageButton,
                      settings.language === lang && styles.activeLanguage,
                    ]}
                    onPress={() => updateSettings({ ...settings, language: lang })}
                  >
                    <Text style={[
                      styles.languageText,
                      settings.language === lang && styles.activeLanguageText,
                    ]}>
                      {lang.toUpperCase()}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Display Unit</Text>
              <View style={styles.unitSelector}>
                {[
                  { key: 'kwh', label: 'kWh' },
                  { key: 'eur', label: '€' },
                ].map((unit) => (
                  <TouchableOpacity
                    key={unit.key}
                    style={[
                      styles.unitButton,
                      settings.currency_unit === unit.key && styles.activeUnit,
                    ]}
                    onPress={() => updateSettings({ ...settings, currency_unit: unit.key })}
                  >
                    <Text style={[
                      styles.unitText,
                      settings.currency_unit === unit.key && styles.activeUnitText,
                    ]}>
                      {unit.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Region (for Subsidies)</Text>
              <View style={styles.regionSelector}>
                {[
                  { key: 'brussels', label: '🏛️ Brussels', flag: '🏛️' },
                  { key: 'wallonia', label: '🌲 Wallonia', flag: '🌲' },
                  { key: 'flanders', label: '🦁 Flanders', flag: '🦁' },
                ].map((region) => (
                  <TouchableOpacity
                    key={region.key}
                    style={[
                      styles.regionButton,
                      settings.region === region.key && styles.activeRegion,
                    ]}
                    onPress={() => updateSettings({ ...settings, region: region.key })}
                  >
                    <Text style={[
                      styles.regionText,
                      settings.region === region.key && styles.activeRegionText,
                    ]}>
                      {region.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        </View>

        {/* Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔔 Notifications</Text>
          
          <View style={styles.settingCard}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.switchLabel}>Push Notifications</Text>
                <Text style={styles.switchDescription}>Receive app notifications</Text>
              </View>
              <Switch
                value={settings.notifications_enabled}
                onValueChange={(value) => 
                  updateSettings({ ...settings, notifications_enabled: value })
                }
                trackColor={{ false: '#333', true: '#4CAF50' }}
                thumbColor={settings.notifications_enabled ? '#fff' : '#ccc'}
              />
            </View>

            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.switchLabel}>High Usage Alerts</Text>
                <Text style={styles.switchDescription}>Alert when usage is above average</Text>
              </View>
              <Switch
                value={settings.high_usage_alerts}
                onValueChange={(value) => 
                  updateSettings({ ...settings, high_usage_alerts: value })
                }
                trackColor={{ false: '#333', true: '#4CAF50' }}
                thumbColor={settings.high_usage_alerts ? '#fff' : '#ccc'}
              />
            </View>

            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.switchLabel}>Weekly Summary</Text>
                <Text style={styles.switchDescription}>Weekly consumption reports</Text>
              </View>
              <Switch
                value={settings.weekly_summary}
                onValueChange={(value) => 
                  updateSettings({ ...settings, weekly_summary: value })
                }
                trackColor={{ false: '#333', true: '#4CAF50' }}
                thumbColor={settings.weekly_summary ? '#fff' : '#ccc'}
              />
            </View>
          </View>
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>ℹ️ About</Text>
          
          <View style={styles.aboutCard}>
            <Text style={styles.aboutTitle}>⚡ Energo Smart</Text>
            <Text style={styles.aboutVersion}>Version 1.0.0 MVP</Text>
            <Text style={styles.aboutDescription}>
              Smart energy management made simple. Track your consumption, save money, and reduce your environmental impact.
            </Text>
            
            <View style={styles.aboutFeatures}>
              <Text style={styles.aboutFeatureTitle}>🔋 Data Sources (MVP)</Text>
              <Text style={styles.aboutFeatureText}>
                Currently using simulated realistic data. Future versions will integrate with:
              </Text>
              <Text style={styles.aboutFeatureItem}>• Fluvius (Flanders)</Text>
              <Text style={styles.aboutFeatureItem}>• ORES (Wallonia)</Text>
              <Text style={styles.aboutFeatureItem}>• Sibelga (Brussels)</Text>
            </View>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.section}>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} disabled={saving}>
            <Text style={styles.logoutButtonText}>🚪 Sign Out</Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>

      {saving && (
        <View style={styles.savingOverlay}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.savingText}>Saving...</Text>
        </View>
      )}
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
  },
  loadingText: {
    color: '#fff',
    marginTop: 16,
    fontSize: 16,
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
  },
  profileCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  userEmail: {
    color: '#999',
    fontSize: 14,
    marginBottom: 8,
  },
  planBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  planText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    marginHorizontal: 20,
  },
  subscriptionContainer: {
    marginHorizontal: 20,
  },
  currentPlanCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  currentPlanTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  currentPlanPrice: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: 'bold',
  },
  upgradeButton: {
    marginBottom: 16,
  },
  upgradeGradient: {
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  upgradeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  upgradeSubtext: {
    color: '#fff',
    fontSize: 12,
    opacity: 0.9,
  },
  planFeaturesContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  featuresTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  featureItem: {
    color: '#4CAF50',
    fontSize: 12,
    marginBottom: 4,
  },
  limitationsTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 12,
    marginBottom: 8,
  },
  limitationItem: {
    color: '#FF9800',
    fontSize: 12,
    marginBottom: 4,
  },
  settingCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  settingLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  languageSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  languageButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#333',
  },
  activeLanguage: {
    backgroundColor: '#4CAF50',
  },
  languageText: {
    color: '#999',
    fontSize: 12,
    fontWeight: '600',
  },
  activeLanguageText: {
    color: '#fff',
  },
  unitSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  unitButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#333',
  },
  activeUnit: {
    backgroundColor: '#4CAF50',
  },
  unitText: {
    color: '#999',
    fontSize: 12,
    fontWeight: '600',
  },
  activeUnitText: {
    color: '#fff',
  },
  regionSelector: {
    flexDirection: 'column',
    gap: 8,
  },
  regionButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: '#333',
    borderWidth: 1,
    borderColor: '#555',
  },
  activeRegion: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  regionText: {
    color: '#999',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  activeRegionText: {
    color: '#fff',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  switchInfo: {
    flex: 1,
    marginRight: 16,
  },
  switchLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  switchDescription: {
    color: '#999',
    fontSize: 12,
  },
  aboutCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  aboutTitle: {
    color: '#4CAF50',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  aboutVersion: {
    color: '#999',
    fontSize: 12,
    marginBottom: 12,
  },
  aboutDescription: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  aboutFeatures: {
    marginTop: 8,
  },
  aboutFeatureTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  aboutFeatureText: {
    color: '#999',
    fontSize: 12,
    marginBottom: 8,
  },
  aboutFeatureItem: {
    color: '#4CAF50',
    fontSize: 12,
    marginBottom: 4,
  },
  logoutButton: {
    backgroundColor: '#ff4444',
    marginHorizontal: 20,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  savingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  savingText: {
    color: '#fff',
    marginTop: 16,
    fontSize: 16,
  },
});