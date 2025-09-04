import React, { useState, useEffect } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Text, Card, ActivityIndicator, SegmentedButtons } from 'react-native-paper';
import { useAuth } from '../services/AuthService';

const AnalyticsScreen = () => {
  const { token, user, API_BASE_URL } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('30');

  const timeframes = [
    { value: '7', label: '7 Days' },
    { value: '30', label: '30 Days' },
    { value: '90', label: '90 Days' },
  ];

  useEffect(() => {
    if (token) {
      fetchAnalytics();
    }
  }, [token, timeframe]);

  const fetchAnalytics = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/analytics/usage?days=${timeframe}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.data.statistics);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <View style={styles.container}>
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.title}>Login Required</Text>
            <Text style={styles.description}>
              Please login to view your analytics dashboard.
            </Text>
          </Card.Content>
        </Card>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Analytics Dashboard</Text>

      <Card style={styles.timeframeCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Timeframe</Text>
          <SegmentedButtons
            value={timeframe}
            onValueChange={setTimeframe}
            buttons={timeframes}
          />
        </Card.Content>
      </Card>

      {analytics && (
        <>
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Usage Overview</Text>
              <View style={styles.statsGrid}>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{analytics.total_events || 0}</Text>
                  <Text style={styles.statLabel}>Total Operations</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{analytics.successful_events || 0}</Text>
                  <Text style={styles.statLabel}>Successful</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statNumber}>{analytics.success_rate || 0}%</Text>
                  <Text style={styles.statLabel}>Success Rate</Text>
                </View>
              </View>
            </Card.Content>
          </Card>

          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Popular Operations</Text>
              {analytics.events_by_type && Object.keys(analytics.events_by_type).length > 0 ? (
                <View style={styles.operationsList}>
                  {Object.entries(analytics.events_by_type)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([operation, count]) => (
                      <View key={operation} style={styles.operationItem}>
                        <Text style={styles.operationName}>
                          {operation.replace('pdf_', '').replace('_', ' ').toUpperCase()}
                        </Text>
                        <View style={styles.operationStats}>
                          <Text style={styles.operationCount}>{count}</Text>
                          <View 
                            style={[
                              styles.operationBar,
                              { 
                                width: `${(count / Math.max(...Object.values(analytics.events_by_type))) * 100}%` 
                              }
                            ]} 
                          />
                        </View>
                      </View>
                    ))}
                </View>
              ) : (
                <Text style={styles.noDataText}>No operations data available</Text>
              )}
            </Card.Content>
          </Card>

          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Daily Activity</Text>
              {analytics.events_by_day && Object.keys(analytics.events_by_day).length > 0 ? (
                <View style={styles.dailyActivity}>
                  {Object.entries(analytics.events_by_day)
                    .sort(([a], [b]) => new Date(b) - new Date(a))
                    .slice(0, 7)
                    .map(([date, count]) => (
                      <View key={date} style={styles.dailyItem}>
                        <Text style={styles.dailyDate}>
                          {new Date(date).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </Text>
                        <Text style={styles.dailyCount}>{count} operations</Text>
                      </View>
                    ))}
                </View>
              ) : (
                <Text style={styles.noDataText}>No daily activity data available</Text>
              )}
            </Card.Content>
          </Card>

          {analytics.most_popular_operation && (
            <Card style={styles.card}>
              <Card.Content>
                <Text style={styles.sectionTitle}>Insights</Text>
                <View style={styles.insight}>
                  <Text style={styles.insightText}>
                    Your most used operation is{' '}
                    <Text style={styles.insightHighlight}>
                      {analytics.most_popular_operation.replace('pdf_', '').replace('_', ' ')}
                    </Text>
                  </Text>
                </View>
                <View style={styles.insight}>
                  <Text style={styles.insightText}>
                    You have a{' '}
                    <Text style={styles.insightHighlight}>
                      {analytics.success_rate}%
                    </Text>
                    {' '}success rate with your operations
                  </Text>
                </View>
              </Card.Content>
            </Card>
          )}
        </>
      )}

      {!analytics && (
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.noDataTitle}>No Data Available</Text>
            <Text style={styles.noDataText}>
              Start using PDF tools to see your analytics here.
            </Text>
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    marginTop: 12,
    color: '#6c757d',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 16,
  },
  timeframeCard: {
    marginBottom: 16,
    elevation: 2,
  },
  card: {
    marginBottom: 16,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007bff',
  },
  statLabel: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 4,
  },
  operationsList: {
    marginTop: 8,
  },
  operationItem: {
    marginBottom: 12,
  },
  operationName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#212529',
    marginBottom: 4,
  },
  operationStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  operationCount: {
    fontSize: 12,
    color: '#6c757d',
    width: 30,
  },
  operationBar: {
    height: 8,
    backgroundColor: '#007bff',
    borderRadius: 4,
    marginLeft: 8,
    flex: 1,
  },
  dailyActivity: {
    marginTop: 8,
  },
  dailyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  dailyDate: {
    fontSize: 14,
    fontWeight: '500',
    color: '#212529',
  },
  dailyCount: {
    fontSize: 14,
    color: '#6c757d',
  },
  insight: {
    marginBottom: 8,
  },
  insightText: {
    fontSize: 14,
    color: '#495057',
    lineHeight: 20,
  },
  insightHighlight: {
    fontWeight: 'bold',
    color: '#007bff',
  },
  noDataTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6c757d',
    textAlign: 'center',
    marginBottom: 8,
  },
  noDataText: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  description: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
  },
});

export default AnalyticsScreen;