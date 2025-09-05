import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthResponse {
  message: string;
  token: string;
  user: User;
}

export default function Index() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      const userData = await AsyncStorage.getItem('energo_user');
      
      if (token && userData) {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
    }
  };

  const handleAuth = async () => {
    if (!email || !password || (!isLogin && !name)) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin 
        ? { email, password }
        : { email, password, name };

      console.log('Making request to:', `${BACKEND_URL}${endpoint}`);
      
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data: AuthResponse = await response.json();
      
      if (response.ok) {
        await AsyncStorage.setItem('energo_token', data.token);
        await AsyncStorage.setItem('energo_user', JSON.stringify(data.user));
        
        setUser(data.user);
        setIsAuthenticated(true);
        
        Alert.alert('Success', data.message);
      } else {
        Alert.alert('Error', data.message || 'Authentication failed');
      }
    } catch (error) {
      console.error('Auth error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('energo_token');
      await AsyncStorage.removeItem('energo_user');
      setUser(null);
      setIsAuthenticated(false);
      setEmail('');
      setPassword('');
      setName('');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Loading state
  if (isAuthenticated === null) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Authenticated user - show welcome/dashboard placeholder
  if (isAuthenticated && user) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <View style={styles.header}>
            <Text style={styles.title}>⚡ Energo</Text>
            <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
              <Text style={styles.logoutText}>Logout</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.welcomeContainer}>
            <Text style={styles.welcomeText}>Welcome back, {user.name}!</Text>
            <Text style={styles.subtitle}>Your Energy Dashboard</Text>
          </View>

          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Today's Consumption</Text>
              <Text style={styles.cardValue}>12.5 kWh</Text>
              <Text style={styles.cardSubtext}>€3.12</Text>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>This Month</Text>
              <Text style={styles.cardValue}>350 kWh</Text>
              <Text style={styles.cardSubtext}>€87.50</Text>
            </View>
          </View>

          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Energy Saved</Text>
              <Text style={styles.cardValue}>8%</Text>
              <Text style={styles.cardSubtext}>vs last month</Text>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardTitle}>Current Rate</Text>
              <Text style={styles.cardValue}>€0.25</Text>
              <Text style={styles.cardSubtext}>per kWh</Text>
            </View>
          </View>

          <View style={styles.statusContainer}>
            <Text style={styles.statusText}>🌱 Energy Saver Badge Unlocked!</Text>
            <Text style={styles.tipText}>💡 Tip: Reduce heating by 1°C to save €15/month</Text>
          </View>

          <TouchableOpacity style={styles.dashboardButton}>
            <Text style={styles.dashboardButtonText}>View Full Dashboard</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Authentication screen
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardContainer}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <View style={styles.authContainer}>
            <Text style={styles.title}>⚡ Energo</Text>
            <Text style={styles.subtitle}>Track Your Energy, Save Money</Text>
            
            <View style={styles.tabContainer}>
              <TouchableOpacity 
                style={[styles.tab, isLogin && styles.activeTab]}
                onPress={() => setIsLogin(true)}
              >
                <Text style={[styles.tabText, isLogin && styles.activeTabText]}>
                  Login
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.tab, !isLogin && styles.activeTab]}
                onPress={() => setIsLogin(false)}
              >
                <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>
                  Sign Up
                </Text>
              </TouchableOpacity>
            </View>

            <View style={styles.formContainer}>
              {!isLogin && (
                <TextInput
                  style={styles.input}
                  placeholder="Full Name"
                  placeholderTextColor="#999"
                  value={name}
                  onChangeText={setName}
                  autoCapitalize="words"
                />
              )}
              
              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor="#999"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor="#999"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoCapitalize="none"
              />
              
              <TouchableOpacity 
                style={styles.authButton}
                onPress={handleAuth}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.authButtonText}>
                    {isLogin ? 'Login' : 'Create Account'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>

            <View style={styles.featuresContainer}>
              <Text style={styles.featuresTitle}>Track & Save Energy</Text>
              <Text style={styles.featureItem}>📊 Real-time consumption monitoring</Text>
              <Text style={styles.featureItem}>💡 AI-powered saving tips</Text>
              <Text style={styles.featureItem}>🏆 Gamification & badges</Text>
              <Text style={styles.featureItem}>📱 Smart notifications</Text>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 20,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4CAF50',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    marginBottom: 40,
  },
  logoutButton: {
    backgroundColor: '#ff4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  logoutText: {
    color: '#fff',
    fontWeight: '600',
  },
  welcomeContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  cardContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    flex: 0.48,
    borderWidth: 1,
    borderColor: '#333',
  },
  cardTitle: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 4,
  },
  cardSubtext: {
    fontSize: 12,
    color: '#666',
  },
  statusContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  statusText: {
    fontSize: 16,
    color: '#4CAF50',
    marginBottom: 8,
    textAlign: 'center',
  },
  tipText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  dashboardButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  dashboardButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 4,
    marginBottom: 30,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#4CAF50',
  },
  tabText: {
    color: '#999',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#fff',
  },
  formContainer: {
    marginBottom: 30,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  authButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 10,
  },
  authButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  featuresContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 16,
    textAlign: 'center',
  },
  featureItem: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
    lineHeight: 20,
  },
});