import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import ToolsScreen from './src/screens/ToolsScreen';
import AccountScreen from './src/screens/AccountScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';

// Import services
import { AuthProvider } from './src/services/AuthService';

const Tab = createBottomTabNavigator();

const theme = {
  colors: {
    primary: '#238287',
    accent: '#28a745',
    background: '#ffffff',
    surface: '#f8f9fa',
    text: '#212529',
  },
};

export default function App() {
  return (
    <AuthProvider>
      <PaperProvider theme={theme}>
        <NavigationContainer>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                let iconName;

                if (route.name === 'Home') {
                  iconName = focused ? 'home' : 'home-outline';
                } else if (route.name === 'Tools') {
                  iconName = focused ? 'build' : 'build-outline';
                } else if (route.name === 'Analytics') {
                  iconName = focused ? 'analytics' : 'analytics-outline';
                } else if (route.name === 'Account') {
                  iconName = focused ? 'person' : 'person-outline';
                }

                return <Ionicons name={iconName} size={size} color={color} />;
              },
              tabBarActiveTintColor: theme.colors.primary,
              tabBarInactiveTintColor: 'gray',
              headerStyle: {
                backgroundColor: theme.colors.primary,
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            })}
          >
            <Tab.Screen 
              name="Home" 
              component={HomeScreen}
              options={{ title: 'PDF Tools' }}
            />
            <Tab.Screen 
              name="Tools" 
              component={ToolsScreen}
              options={{ title: 'Tools' }}
            />
            <Tab.Screen 
              name="Analytics" 
              component={AnalyticsScreen}
              options={{ title: 'Analytics' }}
            />
            <Tab.Screen 
              name="Account" 
              component={AccountScreen}
              options={{ title: 'Account' }}
            />
          </Tab.Navigator>
        </NavigationContainer>
      </PaperProvider>
    </AuthProvider>
  );
}