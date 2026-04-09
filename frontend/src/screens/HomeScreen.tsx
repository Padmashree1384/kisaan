/**
 * HomeScreen — Main dashboard.
 * Shows greeting, trending crops, live mandi prices for watched crops.
 * Pull-to-refresh triggers fresh API call.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl,
  TouchableOpacity, StatusBar, ActivityIndicator, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../services/AuthContext';
import { pricesAPI, PriceRecord } from '../services/api';
import {
  COLORS, SPACING, RADIUS, SHADOWS, TYPOGRAPHY,
  getCropMeta, formatPrice, formatChange, changeColor,
} from '../utils/theme';

export default function HomeScreen({ navigation }: any) {
  const { user } = useAuth();
  const [prices, setPrices] = useState<PriceRecord[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const loadData = useCallback(async () => {
    try {
      const [priceRes, trendRes] = await Promise.all([
        pricesAPI.getPrices({
          state: user?.location_state,
          limit: 20,
        }),
        pricesAPI.getTrending(user?.location_state),
      ]);
      setPrices(priceRes.data);
      setTrending(trendRes.data.slice(0, 5));
    } catch (err: any) {
      if (err?.response?.status !== 401) {
        Alert.alert('Error', 'Could not load prices. Check your connection.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user]);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = () => { setRefreshing(true); loadData(); };

  if (loading) {
    return (
      <View style={styles.loader}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loaderText}>Loading mandi prices...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />}
      showsVerticalScrollIndicator={false}
    >
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />

      {/* Header gradient */}
      <LinearGradient colors={[COLORS.primaryDark, COLORS.primary]} style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.greeting}>{greeting()},</Text>
            <Text style={styles.userName}>{user?.name?.split(' ')[0] ?? 'Farmer'} 👨‍🌾</Text>
            <Text style={styles.location}>📍 {user?.location_district}, {user?.location_state}</Text>
          </View>
          <TouchableOpacity
            style={styles.bellBtn}
            onPress={() => navigation.navigate('Notifications')}
          >
            <Text style={styles.bellIcon}>🔔</Text>
          </TouchableOpacity>
        </View>

        {/* Today's summary pill */}
        <View style={styles.summaryPill}>
          <Text style={styles.summaryText}>
            📊 {prices.length} prices loaded · Tap a crop to see details
          </Text>
        </View>
      </LinearGradient>

      {/* ── Top Movers Section ──────────────────────────────────────────── */}
      {trending.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📈 Top Movers Today</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.trendScroll}>
            {trending.map((item, idx) => {
              const meta = getCropMeta(item.commodity);
              const up = item.change_pct > 0;
              return (
                <View key={idx} style={[styles.trendCard, { backgroundColor: meta.bg }]}>
                  <Text style={styles.trendEmoji}>{meta.emoji}</Text>
                  <Text style={styles.trendCrop} numberOfLines={1}>{item.commodity}</Text>
                  <Text style={styles.trendPrice}>{formatPrice(item.modal_price)}</Text>
                  <View style={[styles.trendBadge, { backgroundColor: up ? COLORS.primaryLight : COLORS.dangerLight }]}>
                    <Text style={[styles.trendChange, { color: up ? COLORS.primary : COLORS.danger }]}>
                      {up ? '▲' : '▼'} {Math.abs(item.change_pct).toFixed(1)}%
                    </Text>
                  </View>
                </View>
              );
            })}
          </ScrollView>
        </View>
      )}

      {/* ── Latest Prices ───────────────────────────────────────────────── */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>🌾 Latest Mandi Prices</Text>
          <TouchableOpacity onPress={loadData}>
            <Text style={styles.refreshLink}>Refresh</Text>
          </TouchableOpacity>
        </View>

        {prices.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyEmoji}>🌱</Text>
            <Text style={styles.emptyText}>No prices yet</Text>
            <Text style={styles.emptySubtext}>Add crops in My Crops to see live prices</Text>
            <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('Crops')}>
              <Text style={styles.addBtnText}>+ Add Crops</Text>
            </TouchableOpacity>
          </View>
        ) : (
          prices.map((item, idx) => <PriceCard key={idx} item={item} />)
        )}
      </View>

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

function PriceCard({ item }: { item: PriceRecord }) {
  const meta = getCropMeta(item.commodity);
  const up = (item.change_pct ?? 0) > 0;
  const pctColor = changeColor(item.change_pct);

  return (
    <View style={styles.priceCard}>
      {/* Left: icon + name */}
      <View style={[styles.cropIconBox, { backgroundColor: meta.bg }]}>
        <Text style={styles.cropEmoji}>{meta.emoji}</Text>
      </View>
      <View style={styles.priceInfo}>
        <Text style={styles.cropName}>{item.commodity}</Text>
        <Text style={styles.mandiName}>📍 {item.market}, {item.district}</Text>
        <View style={styles.minMaxRow}>
          <Text style={styles.minMax}>Min: {formatPrice(item.min_price)}</Text>
          <Text style={styles.minMaxDot}>·</Text>
          <Text style={styles.minMax}>Max: {formatPrice(item.max_price)}</Text>
        </View>
      </View>
      {/* Right: modal price + change */}
      <View style={styles.priceRight}>
        <Text style={styles.modalPrice}>{formatPrice(item.modal_price)}</Text>
        <Text style={styles.perQtl}>/ qtl</Text>
        {item.change_pct !== null && (
          <View style={[styles.changeBadge, { backgroundColor: up ? COLORS.primaryLight : COLORS.dangerLight }]}>
            <Text style={[styles.changeText, { color: pctColor }]}>
              {up ? '▲' : '▼'} {formatChange(item.change_pct)}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  loader: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.background },
  loaderText: { marginTop: 12, color: COLORS.textSecondary, fontSize: 15 },

  header: { paddingTop: 56, paddingBottom: 28, paddingHorizontal: SPACING.lg },
  headerTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  greeting: { fontSize: 14, color: 'rgba(255,255,255,0.7)' },
  userName: { fontSize: 24, fontWeight: '800', color: COLORS.white, marginTop: 2 },
  location: { fontSize: 13, color: 'rgba(255,255,255,0.65)', marginTop: 4 },
  bellBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center', justifyContent: 'center',
  },
  bellIcon: { fontSize: 22 },
  summaryPill: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: RADIUS.pill, paddingHorizontal: 16,
    paddingVertical: 8, alignSelf: 'flex-start', marginTop: 16,
  },
  summaryText: { color: 'rgba(255,255,255,0.9)', fontSize: 13 },

  section: { paddingHorizontal: SPACING.md, paddingTop: SPACING.lg },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: COLORS.textPrimary },
  refreshLink: { fontSize: 13, color: COLORS.primary, fontWeight: '600' },

  trendScroll: { marginLeft: -SPACING.md, paddingLeft: SPACING.md },
  trendCard: {
    width: 120, borderRadius: RADIUS.lg,
    padding: SPACING.md, marginRight: 10,
    alignItems: 'center', ...SHADOWS.card,
  },
  trendEmoji: { fontSize: 32, marginBottom: 6 },
  trendCrop: { fontSize: 13, fontWeight: '600', color: COLORS.textPrimary, textAlign: 'center' },
  trendPrice: { fontSize: 15, fontWeight: '800', color: COLORS.textPrimary, marginTop: 4 },
  trendBadge: { borderRadius: RADIUS.pill, paddingHorizontal: 8, paddingVertical: 3, marginTop: 6 },
  trendChange: { fontSize: 12, fontWeight: '700' },

  priceCard: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.lg,
    padding: SPACING.md, marginBottom: 10,
    flexDirection: 'row', alignItems: 'center',
    ...SHADOWS.card,
  },
  cropIconBox: { width: 52, height: 52, borderRadius: RADIUS.md, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  cropEmoji: { fontSize: 28 },
  priceInfo: { flex: 1 },
  cropName: { fontSize: 16, fontWeight: '700', color: COLORS.textPrimary },
  mandiName: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  minMaxRow: { flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 4 },
  minMax: { fontSize: 11, color: COLORS.textHint },
  minMaxDot: { color: COLORS.textHint, fontSize: 11 },
  priceRight: { alignItems: 'flex-end' },
  modalPrice: { fontSize: 20, fontWeight: '800', color: COLORS.textPrimary },
  perQtl: { fontSize: 11, color: COLORS.textHint },
  changeBadge: { borderRadius: RADIUS.pill, paddingHorizontal: 8, paddingVertical: 3, marginTop: 4 },
  changeText: { fontSize: 12, fontWeight: '700' },

  emptyCard: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.xl,
    padding: SPACING.xl, alignItems: 'center', ...SHADOWS.card,
  },
  emptyEmoji: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 18, fontWeight: '700', color: COLORS.textPrimary },
  emptySubtext: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginTop: 6 },
  addBtn: {
    backgroundColor: COLORS.primary, borderRadius: RADIUS.md,
    paddingHorizontal: 24, paddingVertical: 12, marginTop: 16,
  },
  addBtnText: { color: COLORS.white, fontWeight: '700', fontSize: 15 },
});
