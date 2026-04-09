/**
 * Kisaan Mitra — App.tsx
 * Root component. Sets up navigation, auth provider, and tab bar.
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StatusBar } from 'react-native';

import { AuthProvider } from './src/services/AuthContext';
import SplashScreen from './src/screens/SplashScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import HomeScreen from './src/screens/HomeScreen';
import CropSelectionScreen from './src/screens/CropSelectionScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import { COLORS } from './src/utils/theme';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

/** Tab bar icon component */
function TabIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return (
    <Text style={{ fontSize: focused ? 26 : 22, opacity: focused ? 1 : 0.6 }}>
      {emoji}
    </Text>
  );
}

/** Bottom tab navigator — shown after login */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textHint,
        tabBarStyle: {
          backgroundColor: COLORS.surface,
          borderTopColor: COLORS.border,
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
        headerStyle: { backgroundColor: COLORS.surface },
        headerTitleStyle: { color: COLORS.textPrimary, fontWeight: '700', fontSize: 18 },
        headerShadowVisible: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Dashboard',
          headerShown: false,
          tabBarIcon: ({ focused }) => <TabIcon emoji="🏠" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Crops"
        component={CropSelectionScreen}
        options={{
          title: 'My Crops',
          tabBarIcon: ({ focused }) => <TabIcon emoji="🌾" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          title: 'Alerts',
          tabBarIcon: ({ focused }) => <TabIcon emoji="🔔" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
          tabBarIcon: ({ focused }) => <TabIcon emoji="👤" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  );
}

/** Root stack — handles splash → login/register → main app */
export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <StatusBar barStyle="dark-content" backgroundColor={COLORS.background} />
        <Stack.Navigator
          initialRouteName="Splash"
          screenOptions={{ headerShown: false, animation: 'fade' }}
        >
          <Stack.Screen name="Splash" component={SplashScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
          <Stack.Screen name="MainTabs" component={MainTabs} options={{ animation: 'slide_from_right' }} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthProvider>
  );
}
