/**
 * SplashScreen — shown on app launch.
 * Displays logo, app name, and farming illustration.
 * Navigates to Login or Dashboard based on auth state.
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../services/AuthContext';
import { COLORS, TYPOGRAPHY } from '../utils/theme';

export default function SplashScreen({ navigation }: any) {
  const { isLoading, isAuthenticated } = useAuth();
  const fadeAnim = new Animated.Value(0);
  const slideAnim = new Animated.Value(40);

  useEffect(() => {
    // Entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();

    // Navigate after auth state loads
    const timer = setTimeout(() => {
      if (!isLoading) {
        navigation.replace(isAuthenticated ? 'MainTabs' : 'Login');
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [isLoading, isAuthenticated]);

  return (
    <LinearGradient
      colors={[COLORS.primaryDark, COLORS.primary, '#388E3C']}
      style={styles.container}
    >
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />

      <Animated.View
        style={[
          styles.content,
          { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
        ]}
      >
        {/* Logo area */}
        <View style={styles.logoCircle}>
          <Text style={styles.logoEmoji}>🌾</Text>
        </View>

        {/* App name */}
        <Text style={styles.appName}>ಕಿಸಾನ್ ಮಿತ್ರ</Text>
        <Text style={styles.appNameEn}>Kisaan Mitra</Text>
        <Text style={styles.tagline}>Smart Farmer Assistant</Text>

        {/* Crop emoji row */}
        <View style={styles.emojiRow}>
          {['🍅', '🧅', '🥔', '🌽', '🥜'].map((emoji, i) => (
            <Text key={i} style={styles.cropEmoji}>{emoji}</Text>
          ))}
        </View>
      </Animated.View>

      {/* Bottom tagline */}
      <Animated.View style={[styles.bottom, { opacity: fadeAnim }]}>
        <Text style={styles.bottomText}>Best prices. Best decisions.</Text>
        <Text style={styles.bottomText}>ಅತ್ಯುತ್ತಮ ಬೆಲೆ. ಉತ್ತಮ ನಿರ್ಧಾರ.</Text>
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  logoCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  logoEmoji: {
    fontSize: 60,
  },
  appName: {
    fontSize: 32,
    fontWeight: '800',
    color: COLORS.white,
    letterSpacing: 1,
  },
  appNameEn: {
    fontSize: 22,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
  tagline: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 8,
    letterSpacing: 2,
    textTransform: 'uppercase',
  },
  emojiRow: {
    flexDirection: 'row',
    marginTop: 40,
    gap: 16,
  },
  cropEmoji: {
    fontSize: 32,
  },
  bottom: {
    paddingBottom: 48,
    alignItems: 'center',
  },
  bottomText: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 13,
    marginBottom: 4,
  },
});
