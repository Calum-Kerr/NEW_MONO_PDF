import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Text, Card, Button, FAB } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

const HomeScreen = ({ navigation }) => {
  const quickActions = [
    {
      id: 'merge',
      title: 'Merge PDFs',
      description: 'Combine multiple PDF files into one',
      icon: 'albums-outline',
      color: '#238287',
    },
    {
      id: 'split',
      title: 'Split PDF',
      description: 'Extract pages from PDF documents',
      icon: 'copy-outline',
      color: '#28a745',
    },
    {
      id: 'compress',
      title: 'Compress PDF',
      description: 'Reduce PDF file size',
      icon: 'contract-outline',
      color: '#ffc107',
    },
    {
      id: 'ocr',
      title: 'OCR Text',
      description: 'Extract text from scanned documents',
      icon: 'text-outline',
      color: '#dc3545',
    },
  ];

  const handleQuickAction = (actionId) => {
    navigation.navigate('Tools', { selectedTool: actionId });
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <Text style={styles.welcomeText}>
          Welcome to PDF Tools Mobile
        </Text>
        <Text style={styles.descriptionText}>
          Professional PDF tools in your pocket. Process documents on the go with our mobile app.
        </Text>

        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          {quickActions.map((action) => (
            <Card key={action.id} style={styles.actionCard}>
              <Card.Content>
                <View style={styles.actionContent}>
                  <View style={[styles.iconContainer, { backgroundColor: action.color }]}>
                    <Ionicons name={action.icon} size={24} color="white" />
                  </View>
                  <View style={styles.actionText}>
                    <Text style={styles.actionTitle}>{action.title}</Text>
                    <Text style={styles.actionDescription}>{action.description}</Text>
                  </View>
                  <Button
                    mode="outlined"
                    onPress={() => handleQuickAction(action.id)}
                    style={styles.actionButton}
                  >
                    Use
                  </Button>
                </View>
              </Card.Content>
            </Card>
          ))}
        </View>

        <Card style={styles.featuresCard}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Features</Text>
            <View style={styles.featuresList}>
              <Text style={styles.featureItem}>• Advanced OCR with 20+ languages</Text>
              <Text style={styles.featureItem}>• Batch processing for multiple files</Text>
              <Text style={styles.featureItem}>• Advanced compression algorithms</Text>
              <Text style={styles.featureItem}>• Secure cloud processing</Text>
              <Text style={styles.featureItem}>• Usage analytics and reporting</Text>
            </View>
          </Card.Content>
        </Card>
      </ScrollView>

      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('Tools')}
        label="New Task"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 8,
  },
  descriptionText: {
    fontSize: 16,
    color: '#6c757d',
    marginBottom: 24,
    lineHeight: 22,
  },
  quickActions: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 16,
  },
  actionCard: {
    marginBottom: 12,
    elevation: 2,
  },
  actionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  actionText: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#212529',
  },
  actionDescription: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 2,
  },
  actionButton: {
    marginLeft: 8,
  },
  featuresCard: {
    marginBottom: 80,
    elevation: 2,
  },
  featuresList: {
    marginTop: 8,
  },
  featureItem: {
    fontSize: 14,
    color: '#495057',
    marginBottom: 6,
    lineHeight: 20,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#238287',
  },
});

export default HomeScreen;