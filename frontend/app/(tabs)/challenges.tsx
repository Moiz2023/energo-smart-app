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

interface Challenge {
  id: string;
  title: string;
  description: string;
  target_value: number;
  current_progress: number;
  deadline: string;
  reward_badge: string;
  active: boolean;
}

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  unlocked_at: string | null;
}

interface ChallengesData {
  challenges: Challenge[];
}

interface BadgesData {
  badges: Badge[];
}

export default function Challenges() {
  const [challengesData, setChallengesData] = useState<ChallengesData | null>(null);
  const [badgesData, setBadgesData] = useState<BadgesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'challenges' | 'badges'>('challenges');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = await AsyncStorage.getItem('energo_token');
      if (!token) {
        router.replace('/');
        return;
      }

      const [challengesResponse, badgesResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/challenges`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${BACKEND_URL}/api/badges`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
      ]);

      if (challengesResponse.status === 401 || badgesResponse.status === 401) {
        router.replace('/');
        return;
      }

      if (challengesResponse.ok && badgesResponse.ok) {
        const challenges = await challengesResponse.json();
        const badges = await badgesResponse.json();
        setChallengesData(challenges);
        setBadgesData(badges);
      } else {
        Alert.alert('Error', 'Failed to load challenges and badges');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDeadline = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    if (days > 0) return `${days} days left`;
    return 'Expired';
  };

  const getProgressColor = (progress: number, target: number) => {
    const percentage = (progress / target) * 100;
    if (percentage >= 90) return '#4CAF50';
    if (percentage >= 60) return '#FF9800';
    return '#2196F3';
  };

  const getBadgesByCategory = () => {
    if (!badgesData) return {};
    
    return badgesData.badges.reduce((acc, badge) => {
      if (!acc[badge.category]) {
        acc[badge.category] = [];
      }
      acc[badge.category].push(badge);
      return acc;
    }, {} as Record<string, Badge[]>);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
          <Text style={styles.loadingText}>Loading challenges...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>🏆 Challenges & Badges</Text>
          <Text style={styles.subtitle}>Gamify your energy savings</Text>
        </View>

        {/* Tab Selector */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'challenges' && styles.activeTab]}
            onPress={() => setActiveTab('challenges')}
          >
            <Text style={[styles.tabText, activeTab === 'challenges' && styles.activeTabText]}>
              Challenges
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'badges' && styles.activeTab]}
            onPress={() => setActiveTab('badges')}
          >
            <Text style={[styles.tabText, activeTab === 'badges' && styles.activeTabText]}>
              Badges
            </Text>
          </TouchableOpacity>
        </View>

        {/* Challenges Tab */}
        {activeTab === 'challenges' && challengesData && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>🎯 Active Challenges</Text>
            
            {challengesData.challenges
              .filter(challenge => challenge.active)
              .map((challenge) => {
                const progressPercentage = Math.min((challenge.current_progress / challenge.target_value) * 100, 100);
                const progressColor = getProgressColor(challenge.current_progress, challenge.target_value);
                
                return (
                  <LinearGradient
                    key={challenge.id}
                    colors={['#1a1a1a', '#2a2a2a']}
                    style={styles.challengeCard}
                  >
                    <View style={styles.challengeHeader}>
                      <Text style={styles.challengeTitle}>{challenge.title}</Text>
                      <View style={styles.deadlineContainer}>
                        <Text style={styles.deadlineText}>
                          {formatDeadline(challenge.deadline)}
                        </Text>
                      </View>
                    </View>
                    
                    <Text style={styles.challengeDescription}>
                      {challenge.description}
                    </Text>
                    
                    <View style={styles.progressContainer}>
                      <View style={styles.progressInfo}>
                        <Text style={styles.progressText}>
                          {challenge.current_progress.toFixed(1)} / {challenge.target_value.toFixed(1)}
                        </Text>
                        <Text style={styles.progressPercentage}>
                          {progressPercentage.toFixed(0)}%
                        </Text>
                      </View>
                      
                      <View style={styles.progressBarBackground}>
                        <View
                          style={[
                            styles.progressBarFill,
                            {
                              width: `${progressPercentage}%`,
                              backgroundColor: progressColor,
                            },
                          ]}
                        />
                      </View>
                    </View>
                    
                    <View style={styles.challengeFooter}>
                      <Text style={styles.rewardText}>
                        🏅 Reward: {challenge.reward_badge.replace('_', ' ').toUpperCase()} badge
                      </Text>
                      <TouchableOpacity style={styles.viewDetailsButton}>
                        <Text style={styles.viewDetailsText}>View Details</Text>
                      </TouchableOpacity>
                    </View>
                  </LinearGradient>
                );
              })}

            <Text style={styles.sectionTitle}>💡 Challenge Tips</Text>
            <View style={styles.tipsCard}>
              <Text style={styles.tipsTitle}>How to Complete Challenges</Text>
              <Text style={styles.tipItem}>⚡ Monitor your usage regularly via the dashboard</Text>
              <Text style={styles.tipItem}>🏠 Focus on peak hours (6-9 PM) for maximum impact</Text>
              <Text style={styles.tipItem}>💡 Use AI Assistant recommendations for specific tips</Text>
              <Text style={styles.tipItem}>📱 Enable notifications to track your progress</Text>
            </View>
          </View>
        )}

        {/* Badges Tab */}
        {activeTab === 'badges' && badgesData && (
          <View style={styles.tabContent}>
            <View style={styles.badgeStats}>
              <View style={styles.badgeStatItem}>
                <Text style={styles.badgeStatNumber}>
                  {badgesData.badges.filter(b => b.unlocked_at).length}
                </Text>
                <Text style={styles.badgeStatLabel}>Unlocked</Text>
              </View>
              <View style={styles.badgeStatItem}>
                <Text style={styles.badgeStatNumber}>
                  {badgesData.badges.filter(b => !b.unlocked_at).length}
                </Text>
                <Text style={styles.badgeStatLabel}>To Unlock</Text>
              </View>
              <View style={styles.badgeStatItem}>
                <Text style={styles.badgeStatNumber}>
                  {badgesData.badges.length}
                </Text>
                <Text style={styles.badgeStatLabel}>Total</Text>
              </View>
            </View>

            {Object.entries(getBadgesByCategory()).map(([category, badges]) => (
              <View key={category} style={styles.categorySection}>
                <Text style={styles.categoryTitle}>
                  {category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ')}
                </Text>
                
                <View style={styles.badgesGrid}>
                  {badges.map((badge) => (
                    <View
                      key={badge.id}
                      style={[
                        styles.badgeCard,
                        badge.unlocked_at ? styles.unlockedBadge : styles.lockedBadge,
                      ]}
                    >
                      <Text style={styles.badgeIcon}>{badge.icon}</Text>
                      <Text style={[
                        styles.badgeName,
                        badge.unlocked_at ? styles.unlockedText : styles.lockedText,
                      ]}>
                        {badge.name}
                      </Text>
                      <Text style={[
                        styles.badgeDescription,
                        badge.unlocked_at ? styles.unlockedText : styles.lockedText,
                      ]}>
                        {badge.description}
                      </Text>
                      
                      {badge.unlocked_at && (
                        <Text style={styles.unlockedDate}>
                          Unlocked {new Date(badge.unlocked_at).toLocaleDateString()}
                        </Text>
                      )}
                    </View>
                  ))}
                </View>
              </View>
            ))}
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
  },
  activeTabText: {
    color: '#fff',
  },
  tabContent: {
    paddingHorizontal: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    marginTop: 8,
  },
  challengeCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  challengeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  challengeTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
    marginRight: 12,
  },
  deadlineContainer: {
    backgroundColor: '#FF9800',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  deadlineText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  challengeDescription: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  progressContainer: {
    marginBottom: 16,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  progressPercentage: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: 'bold',
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  challengeFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rewardText: {
    color: '#FF9800',
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  viewDetailsButton: {
    backgroundColor: '#333',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  viewDetailsText: {
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
  badgeStats: {
    flexDirection: 'row',
    backgroundColor: '#1a1a1a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  badgeStatItem: {
    flex: 1,
    alignItems: 'center',
  },
  badgeStatNumber: {
    color: '#4CAF50',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  badgeStatLabel: {
    color: '#999',
    fontSize: 12,
  },
  categorySection: {
    marginBottom: 24,
  },
  categoryTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  badgesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  badgeCard: {
    width: (width - 64) / 2,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  unlockedBadge: {
    backgroundColor: '#1a1a1a',
    borderColor: '#4CAF50',
  },
  lockedBadge: {
    backgroundColor: '#111',
    borderColor: '#333',
  },
  badgeIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  badgeName: {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 4,
  },
  badgeDescription: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 14,
    marginBottom: 8,
  },
  unlockedText: {
    color: '#fff',
  },
  lockedText: {
    color: '#666',
  },
  unlockedDate: {
    color: '#4CAF50',
    fontSize: 10,
    fontWeight: '600',
  },
});