/**
 * AuthContext — global authentication state.
 * Wraps the entire app. Provides login, logout, user object.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authAPI, User, LoginPayload, RegisterPayload } from '../services/api';

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

  // Load persisted auth on app start
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

  const login = async (data: LoginPayload) => {
    const res = await authAPI.login(data);
    await saveAuth(res.data.access_token, res.data.user);
  };

  const register = async (data: RegisterPayload) => {
    const res = await authAPI.register(data);
    await saveAuth(res.data.access_token, res.data.user);
  };

  const logout = async () => {
    await AsyncStorage.multiRemove(['auth_token', 'user_data']);
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const { userAPI } = await import('../services/api');
      const res = await userAPI.getProfile();
      setUser(res.data);
      await AsyncStorage.setItem('user_data', JSON.stringify(res.data));
    } catch (e) {
      console.log('Error refreshing user:', e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
