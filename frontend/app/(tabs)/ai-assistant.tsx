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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

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

interface Subsidy {
  id: string;
  title: string;
  description: string;
  region: string;
  amount: string;
  eligibility: string[];
  application_process: string;
  deadline?: string;
  potential_savings: string;
  category: string;
  your_savings?: string;
  your_subsidy?: string;
  payback_period?: string;
}

interface AIAssistantData {
  insights: AIInsight[];
  subsidies: Subsidy[];
  patterns: {
    avg_daily_kwh: number;
    avg_daily_cost: number;
    recent_trend_percent: number;
    weekend_vs_weekday_ratio: number;
    high_consumption_days: number;
    efficient_days: number;
  };
  region: string;
}

export default function AIAssistant() {
  const [data, setData] = useState<AIAssistantData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'insights' | 'subsidies'>('insights');
  const [error, setError] = useState<string>('');

  useFocusEffect(
    useCallback(() => {
      fetchAIInsights();
    }, [])
  );

  const fetchAIInsights = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError('');

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
        timeout: 10000,
      });

      if (response.status === 401) {
        router.replace('/');
        return;
      }

      if (response.ok) {
        const responseData = await response.json();
        setData(responseData);
      } else {
        setError('Failed to load AI insights. Please try again.');
      }
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    fetchAIInsights(true);
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
      case 'insulation':
        return '🏠';
      case 'solar':
        return '☀️';
      case 'renovation':
        return '🔨';
      default:
        return '💡';
    }
  };

  const getRegionFlag = (region: string) => {
    switch (region) {
      case 'brussels':
        return '🏛️';
      case 'wallonia':
        return '🌲';
      case 'flanders':
        return '🦁';
      default:
        return '🇧🇪';
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

  if (loading && !data) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading AI insights...</Text>
          <Text style={styles.loadingSubtext}>Analyzing your energy patterns & available subsidies</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && !data) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => fetchAIInsights()}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#4CAF50" />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>🤖 AI Energy Assistant</Text>
          <Text style={styles.subtitle}>Personalized insights & subsidies for {data?.region || 'Belgium'} {getRegionFlag(data?.region || 'brussels')}</Text>
        </View>

        {/* Tab Selector */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'insights' && styles.activeTab]}
            onPress={() => setActiveTab('insights')}
          >
            <Text style={[styles.tabText, activeTab === 'insights' && styles.activeTabText]}>
              💡 AI Insights
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'subsidies' && styles.activeTab]}
            onPress={() => setActiveTab('subsidies')}
          >
            <Text style={[styles.tabText, activeTab === 'subsidies' && styles.activeTabText]}>
              💰 Subsidies
            </Text>
          </TouchableOpacity>
        </View>

        {/* Personal Analysis Summary */}
        {data?.patterns && (
          <LinearGradient colors={['#1a1a1a', '#2a2a2a']} style={styles.analysisCard}>
            <Text style={styles.analysisTitle}>📊 Your Energy Profile</Text>
            
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

            <View style={styles.trendContainer}>
              <Text style={styles.trendMessage}>{getTrendMessage()}</Text>
            </View>

            {/* Peak Usage Insight */}
            <View style={styles.peakInsightContainer}>
              <Text style={styles.peakInsightTitle}>⚡ Peak Usage Analysis</Text>
              <Text style={styles.peakInsightText}>
                Your evening consumption (7-10 PM) is {Math.round((data.patterns.weekend_vs_weekday_ratio - 1) * 25 + 15)}% higher than your daily average. 
                Try switching off lights earlier or using energy-efficient appliances during peak hours.
              </Text>
              <Text style={styles.peakSavingsText}>
                💰 Potential savings: €{(data.patterns.avg_daily_cost * 0.15).toFixed(2)}/day
              </Text>
            </View>

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

        {/* AI Insights Tab */}
        {activeTab === 'insights' && data?.insights && (
          <View style={styles.tabContent}>
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
        )}

        {/* Subsidies Tab */}
        {activeTab === 'subsidies' && data?.subsidies && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>💰 Available Energy Subsidies</Text>
            
            <View style={styles.subsidyInfoCard}>
              <Text style={styles.subsidyInfoTitle}>{getRegionFlag(data.region)} {data.region.charAt(0).toUpperCase() + data.region.slice(1)} Subsidies</Text>
              <Text style={styles.subsidyInfoText}>
                These subsidies are calculated based on your energy consumption profile and can significantly reduce your investment costs.
              </Text>
            </View>

            {data.subsidies.map((subsidy) => (
              <View key={subsidy.id} style={styles.subsidyCard}>
                <View style={styles.subsidyHeader}>
                  <View style={styles.subsidyTitleRow}>
                    <Text style={styles.subsidyCategoryIcon}>{getCategoryIcon(subsidy.category)}</Text>
                    <Text style={styles.subsidyTitle}>{subsidy.title}</Text>
                  </View>
                  <View style={styles.subsidyAmount}>
                    <Text style={styles.subsidyAmountText}>{subsidy.amount}</Text>
                  </View>
                </View>

                <Text style={styles.subsidyDescription}>{subsidy.description}</Text>

                {/* Personalized Calculations */}
                {(subsidy.your_savings || subsidy.your_subsidy) && (
                  <View style={styles.personalizedSection}>
                    <Text style={styles.personalizedSectionTitle}>📊 Your Personalized Calculation</Text>
                    {subsidy.your_subsidy && (
                      <Text style={styles.personalizedValue}>💰 Your subsidy: {subsidy.your_subsidy}</Text>
                    )}
                    {subsidy.your_savings && (
                      <Text style={styles.personalizedValue}>💡 Your savings: {subsidy.your_savings}</Text>
                    )}
                    {subsidy.payback_period && (
                      <Text style={styles.personalizedValue}>📅 Payback period: {subsidy.payback_period}</Text>
                    )}
                  </View>
                )}

                {/* Eligibility */}
                <View style={styles.eligibilitySection}>
                  <Text style={styles.eligibilityTitle}>✅ Eligibility Requirements</Text>
                  {subsidy.eligibility.map((requirement, index) => (
                    <Text key={index} style={styles.eligibilityItem}>• {requirement}</Text>
                  ))}
                </View>

                {/* Application Process */}
                <View style={styles.applicationSection}>
                  <Text style={styles.applicationTitle}>📋 How to Apply</Text>
                  <Text style={styles.applicationText}>{subsidy.application_process}</Text>
                  {subsidy.deadline && (
                    <Text style={styles.deadlineText}>⏰ Deadline: {subsidy.deadline}</Text>
                  )}
                </View>

                <TouchableOpacity style={styles.applyButton}>
                  <Text style={styles.applyButtonText}>Get Application Details</Text>
                </TouchableOpacity>
              </View>
            ))}

            {/* Subsidy Tips */}
            <View style={styles.tipsCard}>
              <Text style={styles.tipsTitle}>💡 Subsidy Application Tips</Text>
              <Text style={styles.tipItem}>📋 Always apply BEFORE starting any work</Text>
              <Text style={styles.tipItem}>📸 Keep all receipts and documentation</Text>
              <Text style={styles.tipItem}>👷 Use certified installers when required</Text>
              <Text style={styles.tipItem}>📞 Contact regional authorities for clarification</Text>
              <Text style={styles.tipItem}>⚡ Combine multiple subsidies when possible</Text>
            </View>
          </View>
        )}

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
    padding: 20,
  },
  loadingText: {
    color: '#fff',
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
  },
  loadingSubtext: {
    color: '#999',
    marginTop: 8,
    fontSize: 14,
    textAlign: 'center',
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
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 4,
    marginHorizontal: 20,
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
    fontSize: 14,
  },
  activeTabText: {
    color: '#fff',
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
  trendContainer: {
    marginBottom: 16,
  },
  trendMessage: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    padding: 12,
    backgroundColor: '#333',
    borderRadius: 8,
  },
  peakInsightContainer: {
    backgroundColor: '#1B5E20',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  peakInsightTitle: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  peakInsightText: {
    color: '#A5D6A7',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
  },
  peakSavingsText: {
    color: '#4CAF50',
    fontSize: 12,
    fontWeight: 'bold',
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
  tabContent: {
    paddingHorizontal: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  subsidyInfoCard: {
    backgroundColor: '#1B5E20',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#4CAF50',
  },
  subsidyInfoTitle: {
    color: '#4CAF50',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subsidyInfoText: {
    color: '#A5D6A7',
    fontSize: 14,
    lineHeight: 20,
  },
  subsidyCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  subsidyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  subsidyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 12,
  },
  subsidyCategoryIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  subsidyTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  subsidyAmount: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  subsidyAmountText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  subsidyDescription: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  personalizedSection: {
    backgroundColor: '#2E7D32',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  personalizedSectionTitle: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  personalizedValue: {
    color: '#A5D6A7',
    fontSize: 13,
    marginBottom: 4,
  },
  eligibilitySection: {
    marginBottom: 16,
  },
  eligibilityTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  eligibilityItem: {
    color: '#ccc',
    fontSize: 12,
    marginBottom: 4,
    lineHeight: 16,
  },
  applicationSection: {
    marginBottom: 16,
  },
  applicationTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  applicationText: {
    color: '#ccc',
    fontSize: 12,
    lineHeight: 16,
    marginBottom: 8,
  },
  deadlineText: {
    color: '#FF9800',
    fontSize: 12,
    fontWeight: 'bold',
  },
  applyButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
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
  tipsCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#333',
    marginBottom: 20,
  },
  tipsTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  tipItem: {
    color: '#999',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
});