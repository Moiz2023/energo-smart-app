import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

const { width } = Dimensions.get('window');
const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface AIInsight {
  id: string;
  title: string;
  content: string;
  category: string;
  potential_savings: string;
  priority: string;
  personalized: boolean;
}

interface AIAssistantData {
  insights: AIInsight[];
  patterns: {
    avg_daily_kwh: number;
    avg_daily_cost: number;
    recent_trend_percent: number;
    weekend_vs_weekday_ratio: number;
    high_consumption_days: number;
    efficient_days: number;
  };
}

export default function AIAssistant() {
  const [data, setData] = useState<AIAssistantData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAIInsights();
  }, []);

  const fetchAIInsights = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/ai-insights`, {
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
        const responseData = await response.json();
        setData(responseData);
      } else {
        Alert.alert('Error', 'Failed to load AI insights');
      }
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#FF5722';
      case 'medium':
        return '#FF9800';
      case 'low':
        return '#4CAF50';
      default:
        return '#2196F3';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'welcome':
        return '👋';
      case 'alert':
        return '🚨';
      case 'achievement':
        return '🎉';
      case 'optimization':
        return '⚡';
      case 'timing':
        return '⏰';
      case 'gamification':
        return '🏆';
      case 'heating':
        return '🔥';
      case 'lighting':
        return '💡';
      case 'electronics':
        return '📱';
      case 'appliances':
        return '🏠';
      default:
        return '💡';
    }
  };

  const getTrendMessage = () => {
    if (!data?.patterns) return '';
    
    const trend = data.patterns.recent_trend_percent;
    if (trend > 10) {
      return `⚠️ Your energy usage increased by ${trend.toFixed(1)}% recently`;
    } else if (trend < -5) {
      return `🎉 Great job! You reduced energy usage by ${Math.abs(trend).toFixed(1)}%`;
    } else {
      return `📊 Your energy usage is stable (${trend > 0 ? '+' : ''}${trend.toFixed(1)}%)`;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading AI insights...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!data) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Failed to load AI insights</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchAIInsights}>
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
          <Text style={styles.title}>🤖 AI Energy Assistant</Text>
          <Text style={styles.subtitle}>Personalized insights to save energy</Text>
        </View>

        {/* Personal Analysis Summary */}
        {data.patterns && (
          <LinearGradient colors={['#1a1a1a', '#2a2a2a']} style={styles.analysisCard}>
            <Text style={styles.analysisTitle}>Your Energy Profile</Text>
            
            <View style={styles.analysisRow}>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisValue}>{data.patterns.avg_daily_kwh.toFixed(1)}</Text>
                <Text style={styles.analysisLabel}>Avg Daily kWh</Text>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisValue}>€{data.patterns.avg_daily_cost.toFixed(2)}</Text>
                <Text style={styles.analysisLabel}>Avg Daily Cost</Text>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisValue}>{data.patterns.weekend_vs_weekday_ratio.toFixed(1)}x</Text>
                <Text style={styles.analysisLabel}>Weekend Ratio</Text>
              </View>
            </View>

            <Text style={styles.trendMessage}>{getTrendMessage()}</Text>

            <View style={styles.achievementRow}>
              <View style={styles.achievementItem}>
                <Text style={styles.achievementNumber}>{data.patterns.efficient_days}</Text>
                <Text style={styles.achievementText}>Efficient Days</Text>
              </View>
              <View style={styles.achievementItem}>
                <Text style={styles.achievementNumber}>{data.patterns.high_consumption_days}</Text>
                <Text style={styles.achievementText}>High Usage Days</Text>
              </View>
            </View>
          </LinearGradient>
        )}

        {/* AI Insights */}
        <View style={styles.insightsContainer}>
          <Text style={styles.sectionTitle}>💡 Personalized Insights</Text>
          
          {data.insights.map((insight, index) => (
            <View key={insight.id} style={styles.insightCard}>
              <View style={styles.insightHeader}>
                <View style={styles.insightTitleRow}>
                  <Text style={styles.categoryIcon}>{getCategoryIcon(insight.category)}</Text>
                  <Text style={styles.insightTitle}>{insight.title}</Text>
                </View>
                <View style={styles.insightMeta}>
                  <View 
                    style={[
                      styles.priorityBadge, 
                      { backgroundColor: getPriorityColor(insight.priority) }
                    ]}
                  >
                    <Text style={styles.priorityText}>{insight.priority.toUpperCase()}</Text>
                  </View>
                  {insight.personalized && (
                    <View style={styles.personalizedBadge}>
                      <Text style={styles.personalizedText}>PERSONAL</Text>
                    </View>
                  )}
                </View>
              </View>
              
              <Text style={styles.insightContent}>{insight.content}</Text>
              
              <View style={styles.insightFooter}>
                <Text style={styles.savingsText}>💰 Potential savings: {insight.potential_savings}</Text>
                <TouchableOpacity style={styles.actionButton}>
                  <Text style={styles.actionButtonText}>Learn More</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>

        {/* AI Assistant Info */}
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>How AI Assistant Works</Text>
          <Text style={styles.infoText}>
            Our AI analyzes your energy consumption patterns, seasonal variations, and usage habits to provide personalized recommendations. The insights are updated based on your actual consumption data.
          </Text>
          
          <View style={styles.featuresContainer}>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>📊</Text>
              <Text style={styles.featureText}>Pattern Analysis</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🎯</Text>
              <Text style={styles.featureText}>Personalized Tips</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>🔮</Text>
              <Text style={styles.featureText}>Predictive Insights</Text>
            </View>
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
  analysisCard: {
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  analysisTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  analysisRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  analysisItem: {
    alignItems: 'center',
    flex: 1,
  },
  analysisValue: {
    color: '#4CAF50',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  analysisLabel: {
    color: '#999',
    fontSize: 12,
    textAlign: 'center',
  },
  trendMessage: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#333',
    borderRadius: 8,
  },
  achievementRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  achievementItem: {
    alignItems: 'center',
  },
  achievementNumber: {
    color: '#FF9800',
    fontSize: 24,
    fontWeight: 'bold',
  },
  achievementText: {
    color: '#999',
    fontSize: 12,
    marginTop: 4,
  },
  insightsContainer: {
    paddingHorizontal: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  insightCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  insightHeader: {
    marginBottom: 12,
  },
  insightTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  insightTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  insightMeta: {
    flexDirection: 'row',
    gap: 8,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priorityText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  personalizedBadge: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  personalizedText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  insightContent: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  insightFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  savingsText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  actionButton: {
    backgroundColor: '#333',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  actionButtonText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#1a1a1a',
    marginHorizontal: 20,
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  infoTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  infoText: {
    color: '#999',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  featuresContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  featureItem: {
    alignItems: 'center',
    flex: 1,
  },
  featureIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  featureText: {
    color: '#999',
    fontSize: 12,
    textAlign: 'center',
  },
});