/**
 * Kisaan Mitra — API Service
 * Centralized Axios instance with auth token injection.
 * All backend calls go through this module.
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ── Change this to your backend URL ──────────────────────────────────────────
const BASE_URL = 'https://neutron-talcum-ranger.ngrok-free.dev/api/v1';
//const BASE_URL = 'http://192.168.29.44:8000/api/v1'; // Android emulator
// const BASE_URL = 'http://localhost:8000/api/v1'; // iOS simulator
// const BASE_URL = 'https://your-production-api.com/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach JWT token ─────────────────────────────────────
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 globally ────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.multiRemove(['auth_token', 'user_data']);
      // Navigation to login happens in AuthContext
    }
    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════════
// Auth
// ═══════════════════════════════════════════════════════════════════════════════

export interface RegisterPayload {
  name: string;
  phone: string;
  password: string;
  location_state: string;
  location_district: string;
  language?: string;
  crops?: CropPreference[];
}

export interface LoginPayload {
  phone: string;
  password: string;
}

export interface CropPreference {
  commodity: string;
  state: string;
  district: string;
  market: string;
  alert_enabled: boolean;
}

export interface User {
  id: string;
  name: string;
  phone: string;
  location_state: string;
  location_district: string;
  language: string;
  crops: CropPreference[];
  last_active: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authAPI = {
  register: (data: RegisterPayload): Promise<AxiosResponse<AuthResponse>> =>
    api.post('/register', data),

  login: (data: LoginPayload): Promise<AxiosResponse<AuthResponse>> =>
    api.post('/login', data),
};

// ═══════════════════════════════════════════════════════════════════════════════
// Prices
// ═══════════════════════════════════════════════════════════════════════════════

export interface PriceRecord {
  commodity: string;
  market: string;
  district: string;
  state: string;
  modal_price: number;
  min_price: number;
  max_price: number;
  arrival_date: string;
  change_pct: number | null;
  trend: 'up' | 'down' | 'stable' | null;
}

export interface PriceHistoryPoint {
  date: string;
  modal_price: number;
  min_price: number;
  max_price: number;
}

export const pricesAPI = {
  getPrices: (params: {
    commodity?: string;
    state?: string;
    district?: string;
    market?: string;
    limit?: number;
  }): Promise<AxiosResponse<PriceRecord[]>> =>
    api.get('/prices', { params }),

  getHistory: (commodity: string, market: string, days = 7) =>
    api.get('/prices/history', { params: { commodity, market, days } }),

  getTrending: (state?: string) =>
    api.get('/prices/trending', { params: { state } }),

  manualRefresh: (commodity?: string, state?: string) =>
    api.post('/prices/refresh', null, { params: { commodity, state } }),
};

// ═══════════════════════════════════════════════════════════════════════════════
// Notifications
// ═══════════════════════════════════════════════════════════════════════════════

export interface NotificationRecord {
  id: string;
  alert_type: 'normal' | 'big_jump' | 'inactive' | 'critical';
  commodity: string;
  market: string;
  old_price: number;
  new_price: number;
  change_pct: number;
  message_en: string;
  firebase_sent: boolean;
  sms_sent: boolean;
  status: string;
  created_at: string;
}

export const notificationsAPI = {
  getNotifications: (limit = 20, skip = 0): Promise<AxiosResponse<NotificationRecord[]>> =>
    api.get('/notifications', { params: { limit, skip } }),

  getUnreadCount: () => api.get('/notifications/unread-count'),
};

// ═══════════════════════════════════════════════════════════════════════════════
// User
// ═══════════════════════════════════════════════════════════════════════════════

export const userAPI = {
  getProfile: (): Promise<AxiosResponse<User>> =>
    api.get('/user/profile'),

  updatePreferences: (data: {
    crops?: CropPreference[];
    language?: string;
    location_state?: string;
    location_district?: string;
  }) => api.post('/user/preferences', data),

  updateFcmToken: (fcm_token: string) =>
    api.put('/user/fcm-token', { fcm_token }),
};

export default api;
