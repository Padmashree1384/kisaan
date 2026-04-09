/**
 * ProfileScreen — Farmer's account details, language switch, logout.
 */

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, ActivityIndicator, Switch,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../services/AuthContext';
import { userAPI } from '../services/api';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../utils/theme';

export default function ProfileScreen({ navigation }: any) {
  const { user, logout, refreshUser } = useAuth();
  const [savingLang, setSavingLang] = useState(false);
  const [language, setLanguage] = useState(user?.language ?? 'en');

  const handleLanguageChange = async (lang: string) => {
    setSavingLang(true);
    setLanguage(lang);
    try {
      await userAPI.updatePreferences({ language: lang });
      await refreshUser();
    } catch {
      Alert.alert('Error', 'Could not update language.');
    } finally {
      setSavingLang(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Logout', style: 'destructive', onPress: async () => {
          await logout();
          navigation.replace('Login');
        }},
      ]
    );
  };

  const initials = user?.name
    ?.split(' ')
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() ?? 'KM';

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  const InfoRow = ({ icon, label, value }: { icon: string; label: string; value: string }) => (
    <View style={styles.infoRow}>
      <Text style={styles.infoIcon}>{icon}</Text>
      <View style={styles.infoContent}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
    </View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>

      {/* Hero section */}
      <LinearGradient colors={[COLORS.primaryDark, COLORS.primary]} style={styles.hero}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
        <Text style={styles.heroName}>{user?.name}</Text>
        <Text style={styles.heroPhone}>+91 {user?.phone}</Text>
        <View style={styles.heroBadge}>
          <Text style={styles.heroBadgeText}>👨‍🌾 Kisaan Mitra Farmer</Text>
        </View>
      </LinearGradient>

      {/* Info card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Account Details</Text>
        <InfoRow icon="📱" label="Mobile" value={`+91 ${user?.phone}`} />
        <View style={styles.divider} />
        <InfoRow icon="📍" label="Location" value={`${user?.location_district}, ${user?.location_state}`} />
        <View style={styles.divider} />
        <InfoRow icon="🌾" label="Watched Crops" value={`${user?.crops?.length ?? 0} crops`} />
        <View style={styles.divider} />
        <InfoRow icon="📅" label="Member Since" value={user?.created_at ? formatDate(user.created_at) : '—'} />
      </View>

      {/* Language card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Language / ಭಾಷೆ</Text>
        <View style={styles.langRow}>
          <TouchableOpacity
            style={[styles.langBtn, language === 'en' && styles.langBtnActive]}
            onPress={() => handleLanguageChange('en')}
          >
            <Text style={styles.langFlag}>🇬🇧</Text>
            <Text style={[styles.langText, language === 'en' && styles.langTextActive]}>English</Text>
            {language === 'en' && <Text style={styles.langCheck}>✓</Text>}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.langBtn, language === 'kn' && styles.langBtnActive]}
            onPress={() => handleLanguageChange('kn')}
          >
            <Text style={styles.langFlag}>🇮🇳</Text>
            <Text style={[styles.langText, language === 'kn' && styles.langTextActive]}>ಕನ್ನಡ</Text>
            {language === 'kn' && <Text style={styles.langCheck}>✓</Text>}
          </TouchableOpacity>
        </View>
        {savingLang && (
          <View style={styles.savingRow}>
            <ActivityIndicator size="small" color={COLORS.primary} />
            <Text style={styles.savingText}>Saving...</Text>
          </View>
        )}
      </View>

      {/* Quick actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Quick Actions</Text>
        <TouchableOpacity style={styles.actionRow} onPress={() => navigation.navigate('Crops')}>
          <Text style={styles.actionIcon}>🌾</Text>
          <Text style={styles.actionText}>Manage My Crops</Text>
          <Text style={styles.actionArrow}>›</Text>
        </TouchableOpacity>
        <View style={styles.divider} />
        <TouchableOpacity style={styles.actionRow} onPress={() => navigation.navigate('Notifications')}>
          <Text style={styles.actionIcon}>🔔</Text>
          <Text style={styles.actionText}>Notification History</Text>
          <Text style={styles.actionArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* App info */}
      <View style={[styles.card, styles.infoCard]}>
        <Text style={styles.appInfoTitle}>Kisaan Mitra v1.0</Text>
        <Text style={styles.appInfoText}>
          Built for Indian farmers 🇮🇳{'\n'}
          Prices from AgMarket (data.gov.in){'\n'}
          Alerts via Firebase & Fast2SMS
        </Text>
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { paddingBottom: 60 },
  hero: {
    paddingTop: 56, paddingBottom: 36, alignItems: 'center',
  },
  avatar: {
    width: 88, height: 88, borderRadius: 44,
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 3, borderColor: 'rgba(255,255,255,0.5)',
    marginBottom: 14,
  },
  avatarText: { fontSize: 30, fontWeight: '800', color: COLORS.white },
  heroName: { fontSize: 24, fontWeight: '800', color: COLORS.white },
  heroPhone: { fontSize: 15, color: 'rgba(255,255,255,0.75)', marginTop: 4 },
  heroBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: RADIUS.pill, paddingHorizontal: 16, paddingVertical: 6, marginTop: 12,
  },
  heroBadgeText: { color: COLORS.white, fontSize: 13, fontWeight: '600' },
  card: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.xl,
    marginHorizontal: SPACING.md, marginTop: SPACING.md,
    padding: SPACING.md, ...SHADOWS.card,
  },
  cardTitle: { fontSize: 14, fontWeight: '700', color: COLORS.textSecondary, marginBottom: 14, textTransform: 'uppercase', letterSpacing: 0.5 },
  infoRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  infoIcon: { fontSize: 20, marginRight: 14, width: 28, textAlign: 'center' },
  infoContent: { flex: 1 },
  infoLabel: { fontSize: 12, color: COLORS.textHint, marginBottom: 2 },
  infoValue: { fontSize: 15, color: COLORS.textPrimary, fontWeight: '600' },
  divider: { height: 1, backgroundColor: COLORS.divider, marginLeft: 42 },
  langRow: { flexDirection: 'row', gap: 10 },
  langBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center',
    padding: 14, borderRadius: RADIUS.lg,
    borderWidth: 1.5, borderColor: COLORS.border,
    backgroundColor: COLORS.background, gap: 8,
  },
  langBtnActive: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  langFlag: { fontSize: 20 },
  langText: { flex: 1, fontSize: 14, color: COLORS.textSecondary, fontWeight: '600' },
  langTextActive: { color: COLORS.primary },
  langCheck: { color: COLORS.primary, fontWeight: '800', fontSize: 16 },
  savingRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8 },
  savingText: { color: COLORS.textSecondary, fontSize: 13 },
  actionRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, gap: 12 },
  actionIcon: { fontSize: 22, width: 32, textAlign: 'center' },
  actionText: { flex: 1, fontSize: 15, color: COLORS.textPrimary, fontWeight: '600' },
  actionArrow: { fontSize: 22, color: COLORS.textHint },
  infoCard: { backgroundColor: COLORS.primaryLight },
  appInfoTitle: { fontSize: 14, fontWeight: '700', color: COLORS.primary, marginBottom: 8 },
  appInfoText: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 20 },
  logoutBtn: {
    marginHorizontal: SPACING.md, marginTop: SPACING.md,
    borderWidth: 1.5, borderColor: COLORS.danger,
    borderRadius: RADIUS.lg, padding: 16, alignItems: 'center',
  },
  logoutText: { color: COLORS.danger, fontSize: 15, fontWeight: '700' },
});
