/**
 * LoginScreen — Phone + password login.
 * Shows inline validation, loading state, error messages.
 */

import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, ActivityIndicator,
  KeyboardAvoidingView, Platform, StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../services/AuthContext';
import { COLORS, TYPOGRAPHY, SPACING, RADIUS, SHADOWS } from '../utils/theme';

export default function LoginScreen({ navigation }: any) {
  const { login } = useAuth();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!/^[6-9]\d{9}$/.test(phone)) {
      newErrors.phone = 'Enter a valid 10-digit mobile number';
    }
    if (password.length < 4) {
      newErrors.password = 'Password must be at least 4 characters';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      await login({ phone, password });
      navigation.replace('MainTabs');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Login failed. Please check your credentials.';
      Alert.alert('Login Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />
      <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>

        {/* Header */}
        <LinearGradient
          colors={[COLORS.primaryDark, COLORS.primary]}
          style={styles.header}
        >
          <Text style={styles.logo}>🌾</Text>
          <Text style={styles.appName}>Kisaan Mitra</Text>
          <Text style={styles.subtitle}>ಕಿಸಾನ್ ಮಿತ್ರ</Text>
        </LinearGradient>

        {/* Form Card */}
        <View style={styles.card}>
          <Text style={styles.formTitle}>Welcome Back</Text>
          <Text style={styles.formSubtitle}>Sign in to check today's mandi prices</Text>

          {/* Phone */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Mobile Number</Text>
            <View style={[styles.inputWrapper, errors.phone ? styles.inputError : null]}>
              <Text style={styles.inputPrefix}>+91</Text>
              <TextInput
                style={styles.input}
                placeholder="9876543210"
                placeholderTextColor={COLORS.textHint}
                keyboardType="phone-pad"
                maxLength={10}
                value={phone}
                onChangeText={(v) => { setPhone(v); setErrors(e => ({...e, phone: ''})); }}
              />
            </View>
            {errors.phone ? <Text style={styles.errorText}>{errors.phone}</Text> : null}
          </View>

          {/* Password */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={[styles.inputFull, errors.password ? styles.inputError : null]}
              placeholder="Enter your password"
              placeholderTextColor={COLORS.textHint}
              secureTextEntry
              value={password}
              onChangeText={(v) => { setPassword(v); setErrors(e => ({...e, password: ''})); }}
            />
            {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
          </View>

          {/* Login Button */}
          <TouchableOpacity
            style={[styles.btn, loading && styles.btnDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color={COLORS.white} />
              : <Text style={styles.btnText}>Login 🌾</Text>
            }
          </TouchableOpacity>

          {/* Register link */}
          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={styles.linkText}>
              Don't have an account?{' '}
              <Text style={styles.linkBold}>Register here</Text>
            </Text>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { flexGrow: 1 },
  header: {
    paddingTop: 60, paddingBottom: 40,
    alignItems: 'center',
  },
  logo: { fontSize: 64, marginBottom: 12 },
  appName: { fontSize: 28, fontWeight: '800', color: COLORS.white },
  subtitle: { fontSize: 16, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  card: {
    margin: SPACING.md,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.xl,
    padding: SPACING.lg,
    ...SHADOWS.elevated,
    marginTop: -20,
  },
  formTitle: { ...TYPOGRAPHY.h2, color: COLORS.textPrimary, marginBottom: 4 },
  formSubtitle: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, marginBottom: SPACING.lg },
  inputGroup: { marginBottom: SPACING.md },
  label: {
    fontSize: 13, fontWeight: '600',
    color: COLORS.textSecondary, marginBottom: 6,
    textTransform: 'uppercase', letterSpacing: 0.5,
  },
  inputWrapper: {
    flexDirection: 'row', alignItems: 'center',
    borderWidth: 1.5, borderColor: COLORS.border,
    borderRadius: RADIUS.md, paddingHorizontal: SPACING.md,
    backgroundColor: COLORS.background,
  },
  inputPrefix: { fontSize: 16, color: COLORS.textSecondary, marginRight: 8 },
  input: { flex: 1, height: 52, fontSize: 16, color: COLORS.textPrimary },
  inputFull: {
    borderWidth: 1.5, borderColor: COLORS.border,
    borderRadius: RADIUS.md, paddingHorizontal: SPACING.md,
    height: 52, fontSize: 16, color: COLORS.textPrimary,
    backgroundColor: COLORS.background,
  },
  inputError: { borderColor: COLORS.danger },
  errorText: { color: COLORS.danger, fontSize: 12, marginTop: 4 },
  btn: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    height: 56,
    alignItems: 'center', justifyContent: 'center',
    marginTop: SPACING.md, marginBottom: SPACING.lg,
    ...SHADOWS.card,
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: COLORS.white, fontSize: 17, fontWeight: '700' },
  linkText: { textAlign: 'center', color: COLORS.textSecondary, fontSize: 14 },
  linkBold: { color: COLORS.primary, fontWeight: '700' },
});
