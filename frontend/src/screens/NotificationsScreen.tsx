/**
 * NotificationsScreen — Shows all past alerts for the logged-in farmer.
 * Color-coded by alert type. Shows Firebase/SMS delivery status.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, RefreshControl,
  StatusBar, ActivityIndicator,
} from 'react-native';
import { notificationsAPI, NotificationRecord } from '../services/api';
import { COLORS, SPACING, RADIUS, SHADOWS, getCropMeta, formatPrice } from '../utils/theme';

const ALERT_CONFIG = {
  critical: { icon: '🚨', label: 'Critical Alert', bg: '#FFEBEE', color: '#C62828', border: '#E53935' },
  big_jump: { icon: '📈', label: 'Big Price Jump', bg: '#FFF8E1', color: '#E65100', border: '#FB8C00' },
  normal:   { icon: '💰', label: 'Price Update',   bg: '#E8F5EC', color: '#2D7A45', border: '#43A047' },
  inactive: { icon: '😴', label: 'Reminder',       bg: '#E3F2FD', color: '#1565C0', border: '#1E88E5' },
};

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await notificationsAPI.getNotifications(50);
      setNotifications(res.data);
    } catch (e) {
      console.log('Error loading notifications:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const today = new Date();
    const isToday = d.toDateString() === today.toDateString();
    if (isToday) {
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  };

  const renderItem = ({ item }: { item: NotificationRecord }) => {
    const cfg = ALERT_CONFIG[item.alert_type] ?? ALERT_CONFIG.normal;
    const meta = getCropMeta(item.commodity);
    const pctUp = item.change_pct > 0;

    return (
      <View style={[styles.card, { borderLeftColor: cfg.border }]}>
        <View style={styles.cardTop}>
          {/* Alert type icon + label */}
          <View style={[styles.alertBadge, { backgroundColor: cfg.bg }]}>
            <Text style={styles.alertIcon}>{cfg.icon}</Text>
            <Text style={[styles.alertLabel, { color: cfg.color }]}>{cfg.label}</Text>
          </View>
          <Text style={styles.time}>{formatDate(item.created_at)}</Text>
        </View>

        {/* Commodity + price info */}
        {item.commodity ? (
          <View style={styles.priceRow}>
            <Text style={styles.cropEmoji}>{meta.emoji}</Text>
            <View style={styles.priceInfo}>
              <Text style={styles.commodity}>{item.commodity}</Text>
              <Text style={styles.market}>📍 {item.market}</Text>
            </View>
            <View style={styles.priceChange}>
              <Text style={styles.newPrice}>{formatPrice(item.new_price)}</Text>
              <Text style={[styles.pctChange, { color: pctUp ? COLORS.primary : COLORS.danger }]}>
                {pctUp ? '▲' : '▼'} {Math.abs(item.change_pct).toFixed(1)}%
              </Text>
            </View>
          </View>
        ) : null}

        {/* Message preview */}
        <Text style={styles.message} numberOfLines={2}>{item.message_en}</Text>

        {/* Delivery channels */}
        <View style={styles.deliveryRow}>
          <View style={[styles.pill, { backgroundColor: item.firebase_sent ? COLORS.primaryLight : COLORS.background }]}>
            <Text style={[styles.pillText, { color: item.firebase_sent ? COLORS.primary : COLORS.textHint }]}>
              {item.firebase_sent ? '✓' : '✗'} Push
            </Text>
          </View>
          <View style={[styles.pill, { backgroundColor: item.sms_sent ? '#FFF8E1' : COLORS.background }]}>
            <Text style={[styles.pillText, { color: item.sms_sent ? '#E65100' : COLORS.textHint }]}>
              {item.sms_sent ? '✓' : '✗'} SMS
            </Text>
          </View>
          <View style={[styles.pill, {
            backgroundColor: item.status === 'sent' ? COLORS.primaryLight : COLORS.dangerLight,
          }]}>
            <Text style={[styles.pillText, {
              color: item.status === 'sent' ? COLORS.primary : COLORS.danger,
            }]}>
              {item.status}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loader}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={COLORS.background} />

      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={COLORS.primary} />
        }
        ListHeaderComponent={
          <Text style={styles.header}>🔔 Alert History ({notifications.length})</Text>
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyEmoji}>🔔</Text>
            <Text style={styles.emptyTitle}>No alerts yet</Text>
            <Text style={styles.emptySubtext}>
              You'll see price alerts here once your crops are added and prices update.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  loader: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { padding: SPACING.md, paddingBottom: 40 },
  header: { fontSize: 18, fontWeight: '700', color: COLORS.textPrimary, marginBottom: SPACING.md },
  card: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.lg,
    padding: SPACING.md, marginBottom: 10,
    borderLeftWidth: 4, ...SHADOWS.card,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  alertBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: RADIUS.pill },
  alertIcon: { fontSize: 14 },
  alertLabel: { fontSize: 12, fontWeight: '700' },
  time: { fontSize: 11, color: COLORS.textHint },
  priceRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  cropEmoji: { fontSize: 28, marginRight: 10 },
  priceInfo: { flex: 1 },
  commodity: { fontSize: 15, fontWeight: '700', color: COLORS.textPrimary },
  market: { fontSize: 12, color: COLORS.textSecondary },
  priceChange: { alignItems: 'flex-end' },
  newPrice: { fontSize: 18, fontWeight: '800', color: COLORS.textPrimary },
  pctChange: { fontSize: 13, fontWeight: '700', marginTop: 2 },
  message: { fontSize: 13, color: COLORS.textSecondary, lineHeight: 18, marginBottom: 10 },
  deliveryRow: { flexDirection: 'row', gap: 6 },
  pill: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: RADIUS.pill },
  pillText: { fontSize: 11, fontWeight: '600' },
  empty: { alignItems: 'center', paddingTop: 80 },
  emptyEmoji: { fontSize: 56, marginBottom: 16 },
  emptyTitle: { fontSize: 20, fontWeight: '700', color: COLORS.textPrimary },
  emptySubtext: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', marginTop: 8, paddingHorizontal: 32, lineHeight: 20 },
});
