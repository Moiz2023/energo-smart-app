import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { LineChart, BarChart } from 'react-native-gifted-charts';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const { width } = Dimensions.get('window');
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface DashboardData {
  summary: {
    current_consumption_kwh: number;
    current_cost_euros: number;
    consumption_change_percent: number;
    cost_change_percent: number;
    average_daily_kwh: number;
    average_daily_cost: number;
    period: string;
  };
  insight_card: {
    message: string;
    type: string;
    savings_amount: number;
  };
  progress: {
    weekly_goal_percent: number;
    goal_description: string;
  };
  chart_data: Array<{
    label: string;
    value: number;
    cost: number;
    color: string;
  }>;
}

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    loadUserData();
    fetchDashboardData();
  }, [selectedPeriod]);

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

  const fetchDashboardData = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/dashboard?period=${selectedPeriod}`, {
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
        setDashboardData(data);
      } else {
        Alert.alert('Error', 'Failed to load dashboard data');
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('energo_token');
      await AsyncStorage.removeItem('energo_user');
      router.replace('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const getInsightCardStyle = (type: string) => {
    switch (type) {
      case 'success':
        return { backgroundColor: '#1B5E20', borderColor: '#4CAF50' };
      case 'warning':
        return { backgroundColor: '#E65100', borderColor: '#FF9800' };
      default:
        return { backgroundColor: '#1565C0', borderColor: '#2196F3' };
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '🎉';
      case 'warning':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  const formatChartData = () => {
    if (!dashboardData?.chart_data) return [];
    
    return dashboardData.chart_data.map((item, index) => ({
      value: item.value,
      label: item.label,
      frontColor: item.color,
      gradientColor: item.color,
      spacing: 2,
      labelWidth: 30,
      labelTextStyle: { color: '#999', fontSize: 10 },
    }));
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!dashboardData) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Failed to load dashboard data</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchDashboardData}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.welcomeText}>Welcome back,</Text>
            <Text style={styles.userNameText}>{user?.name || 'User'}!</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>

        {/* Period Selector */}
        <View style={styles.periodSelector}>
          {['day', 'week', 'month'].map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.activePeriodButton,
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text
                style={[
                  styles.periodButtonText,
                  selectedPeriod === period && styles.activePeriodButtonText,
                ]}
              >
                {period.charAt(0).toUpperCase() + period.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Insight Card */}
        <View style={[styles.insightCard, getInsightCardStyle(dashboardData.insight_card.type)]}>
          <Text style={styles.insightIcon}>{getInsightIcon(dashboardData.insight_card.type)}</Text>
          <Text style={styles.insightMessage}>{dashboardData.insight_card.message}</Text>
          {dashboardData.insight_card.savings_amount > 0 && (
            <Text style={styles.savingsAmount}>
              Saved: €{dashboardData.insight_card.savings_amount}
            </Text>
          )}
        </View>

        {/* Summary Cards */}
        <View style={styles.summaryContainer}>
          <LinearGradient colors={['#1a1a1a', '#2a2a2a']} style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Consumption</Text>
            <Text style={styles.summaryValue}>
              {dashboardData.summary.current_consumption_kwh} kWh
            </Text>
            <View style={styles.changeContainer}>
              <Text
                style={[
                  styles.changeText,
                  {
                    color:
                      dashboardData.summary.consumption_change_percent >= 0
                        ? '#FF5722'
                        : '#4CAF50',
                  },
                ]}
              >
                {dashboardData.summary.consumption_change_percent >= 0 ? '↑' : '↓'}
                {Math.abs(dashboardData.summary.consumption_change_percent).toFixed(1)}%
              </Text>
            </View>
          </LinearGradient>

          <LinearGradient colors={['#1a1a1a', '#2a2a2a']} style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Cost</Text>
            <Text style={styles.summaryValue}>
              €{dashboardData.summary.current_cost_euros.toFixed(2)}
            </Text>
            <View style={styles.changeContainer}>
              <Text
                style={[
                  styles.changeText,
                  {
                    color:
                      dashboardData.summary.cost_change_percent >= 0 ? '#FF5722' : '#4CAF50',
                  },
                ]}
              >
                {dashboardData.summary.cost_change_percent >= 0 ? '↑' : '↓'}
                {Math.abs(dashboardData.summary.cost_change_percent).toFixed(1)}%
              </Text>
            </View>
          </LinearGradient>
        </View>

        {/* Progress Tracker */}
        <View style={styles.progressCard}>
          <Text style={styles.progressTitle}>Weekly Energy Goal</Text>
          <View style={styles.progressBarContainer}>
            <View style={styles.progressBarBackground}>
              <View
                style={[
                  styles.progressBarFill,
                  { width: `${Math.min(dashboardData.progress.weekly_goal_percent, 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.progressPercentage}>
              {dashboardData.progress.weekly_goal_percent.toFixed(0)}%
            </Text>
          </View>
          <Text style={styles.progressDescription}>
            {dashboardData.progress.goal_description}
          </Text>
        </View>

        {/* Chart */}
        <View style={styles.chartCard}>
          <Text style={styles.chartTitle}>
            {selectedPeriod === 'day' ? 'Hourly Usage' : 'Daily Usage'}
          </Text>
          <View style={styles.chartContainer}>
            <BarChart
              data={formatChartData()}
              width={width - 80}
              height={200}
              barWidth={selectedPeriod === 'day' ? 12 : 20}
              spacing={selectedPeriod === 'day' ? 8 : 16}
              roundedTop
              roundedBottom
              hideRules
              xAxisThickness={0}
              yAxisThickness={0}
              yAxisTextStyle={{ color: '#666' }}
              noOfSections={4}
              maxValue={Math.max(...(dashboardData.chart_data?.map(d => d.value) || [0])) * 1.1}
            />
          </View>
          
          {/* Chart Legend */}
          <View style={styles.chartLegend}>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#4CAF50' }]} />
              <Text style={styles.legendText}>Below Average</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#FF5722' }]} />
              <Text style={styles.legendText}>Above Average</Text>
            </View>
          </View>
        </View>

        {/* Quick Stats */}
        <View style={styles.quickStatsContainer}>
          <View style={styles.quickStatCard}>
            <Text style={styles.quickStatValue}>
              {dashboardData.summary.average_daily_kwh.toFixed(1)}
            </Text>
            <Text style={styles.quickStatLabel}>Avg Daily kWh</Text>
          </View>
          <View style={styles.quickStatCard}>
            <Text style={styles.quickStatValue}>
              €{dashboardData.summary.average_daily_cost.toFixed(2)}
            </Text>
            <Text style={styles.quickStatLabel}>Avg Daily Cost</Text>
          </View>
          <View style={styles.quickStatCard}>
            <Text style={styles.quickStatValue}>€0.25</Text>
            <Text style={styles.quickStatLabel}>Rate per kWh</Text>
          </View>
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    color: '#ff4444',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 10,
  },
  welcomeText: {
    color: '#999',
    fontSize: 16,
  },
  userNameText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
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
  periodSelector: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 4,
    marginHorizontal: 20,
    marginBottom: 20,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  activePeriodButton: {
    backgroundColor: '#4CAF50',
  },
  periodButtonText: {
    color: '#999',
    fontWeight: '600',
  },
  activePeriodButtonText: {
    color: '#fff',
  },
  insightCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  insightIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  insightMessage: {
    flex: 1,
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  savingsAmount: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: 'bold',
  },
  summaryContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  summaryTitle: {
    color: '#999',
    fontSize: 14,
    marginBottom: 8,
  },
  summaryValue: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  changeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  changeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  progressCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  progressTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  progressBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressBarBackground: {
    flex: 1,
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    marginRight: 12,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 4,
  },
  progressPercentage: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: 'bold',
  },
  progressDescription: {
    color: '#999',
    fontSize: 12,
  },
  chartCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  chartTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  chartContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 2,
    marginRight: 6,
  },
  legendText: {
    color: '#999',
    fontSize: 12,
  },
  quickStatsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  quickStatCard: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
    alignItems: 'center',
  },
  quickStatValue: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  quickStatLabel: {
    color: '#999',
    fontSize: 11,
    textAlign: 'center',
  },
});