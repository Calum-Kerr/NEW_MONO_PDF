import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, Alert } from 'react-native';
import { 
  Text, 
  Card, 
  Button, 
  TextInput, 
  Switch, 
  List,
  Divider,
  Avatar
} from 'react-native-paper';
import { useAuth } from '../services/AuthService';

const AccountScreen = () => {
  const { user, logout } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoBackup, setAutoBackup] = useState(false);

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            setIsLoggingOut(true);
            try {
              await logout();
            } catch (error) {
              Alert.alert('Error', 'Failed to logout');
            } finally {
              setIsLoggingOut(false);
            }
          },
        },
      ]
    );
  };

  const handleUpgrade = () => {
    Alert.alert(
      'Upgrade to Pro',
      'Get unlimited operations, advanced features, and priority support.',
      [
        { text: 'Maybe Later', style: 'cancel' },
        { text: 'Upgrade Now', onPress: () => console.log('Upgrade') },
      ]
    );
  };

  if (!user) {
    return (
      <View style={styles.container}>
        <Card style={styles.loginCard}>
          <Card.Content>
            <Avatar.Icon 
              size={80} 
              icon="account" 
              style={styles.avatar} 
            />
            <Text style={styles.loginTitle}>Welcome to PDF Tools</Text>
            <Text style={styles.loginDescription}>
              Login to access your account, view analytics, and manage your API keys.
            </Text>
            
            <View style={styles.loginForm}>
              <TextInput
                label="Email"
                mode="outlined"
                style={styles.input}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              <TextInput
                label="Password"
                mode="outlined"
                style={styles.input}
                secureTextEntry
              />
              <Button 
                mode="contained" 
                style={styles.loginButton}
                onPress={() => Alert.alert('Info', 'Login functionality would be implemented here')}
              >
                Login
              </Button>
              <Button 
                mode="outlined" 
                style={styles.registerButton}
                onPress={() => Alert.alert('Info', 'Registration functionality would be implemented here')}
              >
                Create Account
              </Button>
            </View>
          </Card.Content>
        </Card>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.profileCard}>
        <Card.Content>
          <View style={styles.profileHeader}>
            <Avatar.Text 
              size={60} 
              label={user.email?.charAt(0).toUpperCase() || 'U'} 
              style={styles.profileAvatar}
            />
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>{user.email}</Text>
              <Text style={styles.profileStatus}>Free Plan</Text>
            </View>
          </View>
          
          <Button 
            mode="contained" 
            icon="star"
            style={styles.upgradeButton}
            onPress={handleUpgrade}
          >
            Upgrade to Pro
          </Button>
        </Card.Content>
      </Card>

      <Card style={styles.usageCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Usage This Month</Text>
          <View style={styles.usageStats}>
            <View style={styles.usageStat}>
              <Text style={styles.usageNumber}>12</Text>
              <Text style={styles.usageLabel}>Operations Used</Text>
            </View>
            <View style={styles.usageStat}>
              <Text style={styles.usageNumber}>5</Text>
              <Text style={styles.usageLabel}>Remaining</Text>
            </View>
          </View>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: '70%' }]} />
          </View>
          <Text style={styles.progressText}>70% of free quota used</Text>
        </Card.Content>
      </Card>

      <Card style={styles.settingsCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Settings</Text>
          
          <List.Item
            title="Notifications"
            description="Receive updates about your operations"
            left={props => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={notificationsEnabled}
                onValueChange={setNotificationsEnabled}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Auto Backup"
            description="Automatically backup processed files"
            left={props => <List.Icon {...props} icon="backup-restore" />}
            right={() => (
              <Switch
                value={autoBackup}
                onValueChange={setAutoBackup}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="API Keys"
            description="Manage your API access"
            left={props => <List.Icon {...props} icon="key" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => Alert.alert('Info', 'API Keys management would open here')}
          />
          
          <Divider />
          
          <List.Item
            title="Storage"
            description="Manage your file storage"
            left={props => <List.Icon {...props} icon="folder" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => Alert.alert('Info', 'Storage management would open here')}
          />
        </Card.Content>
      </Card>

      <Card style={styles.supportCard}>
        <Card.Content>
          <Text style={styles.sectionTitle}>Support</Text>
          
          <List.Item
            title="Help Center"
            description="Find answers to common questions"
            left={props => <List.Icon {...props} icon="help-circle" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => Alert.alert('Info', 'Help center would open here')}
          />
          
          <Divider />
          
          <List.Item
            title="Contact Support"
            description="Get help from our team"
            left={props => <List.Icon {...props} icon="message" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => Alert.alert('Info', 'Support contact would open here')}
          />
          
          <Divider />
          
          <List.Item
            title="Privacy Policy"
            description="Read our privacy policy"
            left={props => <List.Icon {...props} icon="shield-check" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => Alert.alert('Info', 'Privacy policy would open here')}
          />
        </Card.Content>
      </Card>

      <Card style={styles.logoutCard}>
        <Card.Content>
          <Button 
            mode="outlined" 
            icon="logout"
            style={styles.logoutButton}
            loading={isLoggingOut}
            disabled={isLoggingOut}
            onPress={handleLogout}
          >
            {isLoggingOut ? 'Logging Out...' : 'Logout'}
          </Button>
        </Card.Content>
      </Card>

      <View style={styles.footer}>
        <Text style={styles.footerText}>PDF Tools Mobile v1.0.0</Text>
        <Text style={styles.footerText}>© 2024 PDF Tools Platform</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
  },
  loginCard: {
    marginTop: 40,
    elevation: 2,
  },
  avatar: {
    alignSelf: 'center',
    marginBottom: 16,
    backgroundColor: '#238287',
  },
  loginTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#212529',
    marginBottom: 8,
  },
  loginDescription: {
    fontSize: 14,
    textAlign: 'center',
    color: '#6c757d',
    marginBottom: 24,
    lineHeight: 20,
  },
  loginForm: {
    marginTop: 16,
  },
  input: {
    marginBottom: 12,
  },
  loginButton: {
    marginTop: 8,
    marginBottom: 12,
  },
  registerButton: {
    marginBottom: 8,
  },
  profileCard: {
    marginBottom: 16,
    elevation: 2,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  profileAvatar: {
    backgroundColor: '#238287',
    marginRight: 16,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212529',
  },
  profileStatus: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 2,
  },
  upgradeButton: {
    backgroundColor: '#28a745',
  },
  usageCard: {
    marginBottom: 16,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#212529',
    marginBottom: 12,
  },
  usageStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  usageStat: {
    alignItems: 'center',
  },
  usageNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#238287',
  },
  usageLabel: {
    fontSize: 12,
    color: '#6c757d',
    marginTop: 4,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e9ecef',
    borderRadius: 4,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#238287',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    color: '#6c757d',
    textAlign: 'center',
  },
  settingsCard: {
    marginBottom: 16,
    elevation: 2,
  },
  supportCard: {
    marginBottom: 16,
    elevation: 2,
  },
  logoutCard: {
    marginBottom: 16,
    elevation: 2,
  },
  logoutButton: {
    borderColor: '#dc3545',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  footerText: {
    fontSize: 12,
    color: '#6c757d',
    marginBottom: 4,
  },
});

export default AccountScreen;