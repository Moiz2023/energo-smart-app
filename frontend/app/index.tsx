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
import { router } from 'expo-router';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  email: string;
  name: string;
  settings?: any;
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
  const [initialLoading, setInitialLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [loginError, setLoginError] = useState<string>('');
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      console.log('Checking auth status...');
      console.log('Backend URL:', BACKEND_URL);
      
      const token = await AsyncStorage.getItem('energo_token');
      const userData = await AsyncStorage.getItem('energo_user');
      
      console.log('Token exists:', !!token);
      console.log('User data exists:', !!userData);
      
      if (token && userData) {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
        // Navigate to dashboard immediately
        setTimeout(() => {
          router.replace('/(tabs)/dashboard');
        }, 100);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
    } finally {
      console.log('Auth check complete, setting initialLoading to false');
      setInitialLoading(false);
    }
  };

  const validateForm = () => {
    setLoginError('');
    
    if (!email.trim()) {
      setLoginError('Please enter your email');
      return false;
    }
    
    if (!email.includes('@')) {
      setLoginError('Please enter a valid email address');
      return false;
    }
    
    if (!password.trim()) {
      setLoginError('Please enter your password');
      return false;
    }
    
    if (password.length < 6) {
      setLoginError('Password must be at least 6 characters');
      return false;
    }
    
    if (!isLogin && !name.trim()) {
      setLoginError('Please enter your full name');
      return false;
    }
    
    return true;
  };

  const handleAuth = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setLoginError('');
    
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const body = isLogin 
        ? { email: email.trim().toLowerCase(), password }
        : { email: email.trim().toLowerCase(), password, name: name.trim() };

      console.log('Attempting authentication:', endpoint);
      
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        
      });

      const data: AuthResponse = await response.json();
      
      if (response.ok) {
        console.log('Authentication successful');
        
        // Store authentication data
        await AsyncStorage.setItem('energo_token', data.token);
        await AsyncStorage.setItem('energo_user', JSON.stringify(data.user));
        
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Clear form
        setEmail('');
        setPassword('');
        setName('');
        
        // Navigate to dashboard with a small delay to ensure state is updated
        setTimeout(() => {
          router.replace('/(tabs)/dashboard');
        }, 100);
        
      } else {
        // Handle specific error cases
        if (response.status === 401) {
          setLoginError('Invalid email or password. Please try again.');
        } else if (response.status === 400) {
          setLoginError(data.message || 'Please check your information and try again.');
        } else {
          setLoginError('Authentication failed. Please try again.');
        }
      }
    } catch (error) {
      console.error('Auth error:', error);
      if ((error as any).name === 'AbortError' || (error as any).message?.includes?.('timeout')) {
        setLoginError('Connection timeout. Please check your internet and try again.');
      } else {
        setLoginError('Network error. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLoginFallback = () => {
    Alert.alert(
      'Social Login Unavailable',
      'Social login is currently unavailable. Please use email and password to continue.',
      [{ text: 'OK' }]
    );
  };

  // Initial loading state
  if (initialLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.title}>⚡ Energo Smart</Text>
          <ActivityIndicator size="large" color="#4CAF50" style={styles.loader} />
          <Text style={styles.loadingText}>Initializing...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // If authenticated, this component shouldn't be visible (will redirect)
  if (isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.title}>⚡ Energo Smart</Text>
          <ActivityIndicator size="large" color="#4CAF50" style={styles.loader} />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
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
        <ScrollView 
          contentContainerStyle={styles.scrollContainer}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.authContainer}>
            <Text style={styles.title}>⚡ Energo Smart</Text>
            <Text style={styles.subtitle}>Smart Energy Management</Text>
            
            <View style={styles.tabContainer}>
              <TouchableOpacity 
                style={[styles.tab, isLogin && styles.activeTab]}
                onPress={() => {
                  setIsLogin(true);
                  setLoginError('');
                }}
              >
                <Text style={[styles.tabText, isLogin && styles.activeTabText]}>
                  Login
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.tab, !isLogin && styles.activeTab]}
                onPress={() => {
                  setIsLogin(false);
                  setLoginError('');
                }}
              >
                <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>
                  Sign Up
                </Text>
              </TouchableOpacity>
            </View>

            {/* Error Message */}
            {loginError ? (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>⚠️ {loginError}</Text>
              </View>
            ) : null}

            <View style={styles.formContainer}>
              {!isLogin && (
                <TextInput
                  style={styles.input}
                  placeholder="Full Name"
                  placeholderTextColor="#999"
                  value={name}
                  onChangeText={(text) => {
                    setName(text);
                    setLoginError('');
                  }}
                  autoCapitalize="words"
                  editable={!loading}
                />
              )}
              
              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor="#999"
                value={email}
                onChangeText={(text) => {
                  setEmail(text);
                  setLoginError('');
                }}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading}
              />
              
              <TextInput
                style={styles.input}
                placeholder="Password (min 6 characters)"
                placeholderTextColor="#999"
                value={password}
                onChangeText={(text) => {
                  setPassword(text);
                  setLoginError('');
                }}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading}
              />
              
              <TouchableOpacity 
                style={[styles.authButton, loading && styles.authButtonDisabled]}
                onPress={handleAuth}
                disabled={loading}
              >
                {loading ? (
                  <View style={styles.buttonLoadingContainer}>
                    <ActivityIndicator color="#fff" size="small" />
                    <Text style={styles.authButtonText}>
                      {isLogin ? 'Signing in...' : 'Creating account...'}
                    </Text>
                  </View>
                ) : (
                  <Text style={styles.authButtonText}>
                    {isLogin ? 'Sign In' : 'Create Account'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>

            {/* Social Login Placeholder */}
            <View style={styles.socialContainer}>
              <TouchableOpacity 
                style={styles.socialButton}
                onPress={handleSocialLoginFallback}
                disabled={loading}
              >
                <Text style={styles.socialButtonText}>🔐 Google Login (Coming Soon)</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.socialButton}
                onPress={handleSocialLoginFallback}
                disabled={loading}
              >
                <Text style={styles.socialButtonText}>🍎 Apple Login (Coming Soon)</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.featuresContainer}>
              <Text style={styles.featuresTitle}>Smart Energy Features</Text>
              <Text style={styles.featureItem}>📊 Real-time consumption analytics</Text>
              <Text style={styles.featureItem}>💡 AI-powered personalized tips</Text>
              <Text style={styles.featureItem}>🏆 Gamification & achievements</Text>
              <Text style={styles.featureItem}>📱 Smart notifications & alerts</Text>
              <Text style={styles.featureItem}>📈 Predictive insights & forecasting</Text>
            </View>

            {/* Demo Account Info */}
            <View style={styles.demoContainer}>
              <Text style={styles.demoTitle}>🚀 Quick Demo</Text>
              <Text style={styles.demoText}>
                Try the demo with: demo@energo.com / password123
              </Text>
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
  loader: {
    marginVertical: 20,
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
    minHeight: 600,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#4CAF50',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 18,
    color: '#999',
    textAlign: 'center',
    marginBottom: 40,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
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
  errorContainer: {
    backgroundColor: '#3D1A1A',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FF5252',
  },
  errorText: {
    color: '#FF5252',
    fontSize: 14,
    textAlign: 'center',
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
  authButtonDisabled: {
    backgroundColor: '#2E7D32',
    opacity: 0.7,
  },
  buttonLoadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  authButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  socialContainer: {
    marginBottom: 30,
    gap: 12,
  },
  socialButton: {
    backgroundColor: '#333',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#555',
  },
  socialButtonText: {
    color: '#999',
    fontSize: 14,
    fontWeight: '600',
  },
  featuresContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#333',
    marginBottom: 20,
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
  demoContainer: {
    backgroundColor: '#1A3D1A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  demoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 8,
    textAlign: 'center',
  },
  demoText: {
    fontSize: 12,
    color: '#A5D6A7',
    textAlign: 'center',
    lineHeight: 16,
  },
});