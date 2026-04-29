import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { authAPI, userAPI, User, LoginPayload, RegisterPayload } from '../services/api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const [storedToken, storedUser] = await AsyncStorage.multiGet([
        'auth_token',
        'user_data',
      ]);
      if (storedToken[1] && storedUser[1]) {
        setToken(storedToken[1]);
        setUser(JSON.parse(storedUser[1]));
        await registerForPushNotifications();
      }
    } catch (e) {
      console.log('Error loading auth:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const saveAuth = async (newToken: string, newUser: User) => {
    await AsyncStorage.multiSet([
      ['auth_token', newToken],
      ['user_data', JSON.stringify(newUser)],
    ]);
    setToken(newToken);
    setUser(newUser);
  };

  const registerForPushNotifications = async () => {
    try {
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('kisaan-mitra', {
          name: 'Kisaan Mitra Alerts',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#2D7A45',
          sound: 'default',
        });
      }

      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      if (finalStatus !== 'granted') {
        console.log('⚠️ Notification permission denied');
        return;
      }

      // Get Expo push token with projectId
      const pushToken = await Notifications.getExpoPushTokenAsync({
        projectId: 'ed7aed5e-dfdb-4db8-96ad-8980260ec263',
      });

      const fcmToken = pushToken.data;
      console.log('📱 Push token:', fcmToken);

      await userAPI.updateFcmToken(fcmToken);
      console.log('✅ FCM token saved to backend!');

    } catch (e) {
      console.log('⚠️ Push notification setup failed:', e);
    }
  };

  const login = async (data: LoginPayload) => {
    const res = await authAPI.login(data);
    await saveAuth(res.data.access_token, res.data.user);
    await registerForPushNotifications();
  };

  const register = async (data: RegisterPayload) => {
    const res = await authAPI.register(data);
    await saveAuth(res.data.access_token, res.data.user);
    await registerForPushNotifications();
  };

  const logout = async () => {
    await AsyncStorage.multiRemove(['auth_token', 'user_data']);
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const res = await userAPI.getProfile();
      setUser(res.data);
      await AsyncStorage.setItem('user_data', JSON.stringify(res.data));
    } catch (e) {
      console.log('Error refreshing user:', e);
    }
  };

  return (
    <AuthContext.Provider value={{
      user, token, isLoading,
      isAuthenticated: !!token && !!user,
      login, register, logout, refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};