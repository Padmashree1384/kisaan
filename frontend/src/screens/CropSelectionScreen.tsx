/**
 * CropSelectionScreen — Farmer selects which crops & mandis to watch.
 * Saved to user preferences via POST /user/preferences.
 */

import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, Alert, ActivityIndicator, Switch,
} from 'react-native';
import { userAPI, CropPreference } from '../services/api';
import { useAuth } from '../services/AuthContext';
import { COLORS, SPACING, RADIUS, SHADOWS, getCropMeta } from '../utils/theme';

const AVAILABLE_CROPS = [
  'Tomato', 'Onion', 'Potato', 'Rice', 'Paddy', 'Maize',
  'Wheat', 'Groundnut', 'Soyabean', 'Brinjal', 'Cabbage',
  'Cauliflower', 'Chilli', 'Turmeric', 'Ginger',
];

const KARNATAKA_MARKETS = [
  'Bengaluru', 'Mysuru', 'Hubballi', 'Davangere', 'Raichur',
  'Bidar', 'Hassan', 'Tumakuru', 'Shimoga', 'Dharwad',
];

export default function CropSelectionScreen({ navigation }: any) {
  const { user, refreshUser } = useAuth();
  const [crops, setCrops] = useState<CropPreference[]>(user?.crops ?? []);
  const [saving, setSaving] = useState(false);
  const [editIdx, setEditIdx] = useState<number | null>(null);
  const [newCrop, setNewCrop] = useState('');
  const [newMarket, setNewMarket] = useState('');
  const [newState] = useState(user?.location_state ?? 'Karnataka');
  const [newDistrict] = useState(user?.location_district ?? '');
  const [showAddForm, setShowAddForm] = useState(false);

  const addCrop = () => {
    if (!newCrop || !newMarket) {
      Alert.alert('Missing Info', 'Please select a crop and a market.');
      return;
    }
    const exists = crops.find(c => c.commodity === newCrop && c.market === newMarket);
    if (exists) {
      Alert.alert('Already added', `${newCrop} at ${newMarket} is already in your list.`);
      return;
    }
    setCrops(prev => [...prev, {
      commodity: newCrop,
      state: newState,
      district: newDistrict,
      market: newMarket,
      alert_enabled: true,
    }]);
    setNewCrop('');
    setNewMarket('');
    setShowAddForm(false);
  };

  const removeCrop = (idx: number) => {
    Alert.alert('Remove Crop', `Remove ${crops[idx].commodity} from your watchlist?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: () => setCrops(c => c.filter((_, i) => i !== idx)) },
    ]);
  };

  const toggleAlert = (idx: number) => {
    setCrops(prev => prev.map((c, i) => i === idx ? { ...c, alert_enabled: !c.alert_enabled } : c));
  };

  const savePreferences = async () => {
    setSaving(true);
    try {
      await userAPI.updatePreferences({ crops });
      await refreshUser();
      Alert.alert('Saved! 🌱', 'Your crop preferences have been updated.');
      navigation.goBack();
    } catch (err) {
      Alert.alert('Error', 'Could not save preferences. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.pageTitle}>🌾 My Crops</Text>
      <Text style={styles.pageSubtitle}>
        Select crops and mandis to get live price alerts
      </Text>

      {/* Existing crops */}
      {crops.map((crop, idx) => {
        const meta = getCropMeta(crop.commodity);
        return (
          <View key={idx} style={styles.cropCard}>
            <View style={[styles.cropIcon, { backgroundColor: meta.bg }]}>
              <Text style={styles.cropEmoji}>{meta.emoji}</Text>
            </View>
            <View style={styles.cropInfo}>
              <Text style={styles.cropName}>{crop.commodity}</Text>
              <Text style={styles.mandiName}>📍 {crop.market}, {crop.state}</Text>
            </View>
            <View style={styles.cropActions}>
              <Switch
                value={crop.alert_enabled}
                onValueChange={() => toggleAlert(idx)}
                trackColor={{ false: COLORS.border, true: COLORS.primaryMid }}
                thumbColor={crop.alert_enabled ? COLORS.primary : COLORS.textHint}
                style={{ transform: [{ scaleX: 0.85 }, { scaleY: 0.85 }] }}
              />
              <TouchableOpacity onPress={() => removeCrop(idx)} style={styles.removeBtn}>
                <Text style={styles.removeBtnText}>✕</Text>
              </TouchableOpacity>
            </View>
          </View>
        );
      })}

      {/* Add crop form */}
      {showAddForm ? (
        <View style={styles.addForm}>
          <Text style={styles.addFormTitle}>Add a Crop</Text>

          {/* Crop picker */}
          <Text style={styles.label}>Select Crop</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
            {AVAILABLE_CROPS.map(crop => (
              <TouchableOpacity
                key={crop}
                style={[styles.chip, newCrop === crop && styles.chipActive]}
                onPress={() => setNewCrop(crop)}
              >
                <Text style={styles.chipEmoji}>{getCropMeta(crop).emoji}</Text>
                <Text style={[styles.chipText, newCrop === crop && styles.chipTextActive]}>{crop}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Market picker */}
          <Text style={styles.label}>Select Market (Mandi)</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
            {KARNATAKA_MARKETS.map(m => (
              <TouchableOpacity
                key={m}
                style={[styles.marketChip, newMarket === m && styles.chipActive]}
                onPress={() => setNewMarket(m)}
              >
                <Text style={[styles.chipText, newMarket === m && styles.chipTextActive]}>
                  📍 {m}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <View style={styles.addFormBtns}>
            <TouchableOpacity style={styles.cancelBtn} onPress={() => setShowAddForm(false)}>
              <Text style={styles.cancelBtnText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.confirmBtn} onPress={addCrop}>
              <Text style={styles.confirmBtnText}>Add Crop ✓</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <TouchableOpacity style={styles.addCropBtn} onPress={() => setShowAddForm(true)}>
          <Text style={styles.addCropBtnText}>+ Add Crop</Text>
        </TouchableOpacity>
      )}

      {/* Save button */}
      <TouchableOpacity
        style={[styles.saveBtn, saving && styles.btnDisabled]}
        onPress={savePreferences}
        disabled={saving}
      >
        {saving
          ? <ActivityIndicator color={COLORS.white} />
          : <Text style={styles.saveBtnText}>Save Preferences 💾</Text>
        }
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: SPACING.md, paddingBottom: 60 },
  pageTitle: { fontSize: 24, fontWeight: '800', color: COLORS.textPrimary, marginBottom: 4 },
  pageSubtitle: { fontSize: 14, color: COLORS.textSecondary, marginBottom: SPACING.lg, lineHeight: 20 },
  cropCard: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.lg,
    padding: SPACING.md, marginBottom: 10,
    flexDirection: 'row', alignItems: 'center',
    ...SHADOWS.card,
  },
  cropIcon: { width: 48, height: 48, borderRadius: RADIUS.md, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  cropEmoji: { fontSize: 26 },
  cropInfo: { flex: 1 },
  cropName: { fontSize: 16, fontWeight: '700', color: COLORS.textPrimary },
  mandiName: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  cropActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  removeBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.dangerLight, alignItems: 'center', justifyContent: 'center' },
  removeBtnText: { color: COLORS.danger, fontSize: 12, fontWeight: '700' },
  addCropBtn: {
    borderWidth: 2, borderStyle: 'dashed', borderColor: COLORS.primary,
    borderRadius: RADIUS.lg, padding: SPACING.md,
    alignItems: 'center', marginBottom: SPACING.md,
  },
  addCropBtnText: { color: COLORS.primary, fontWeight: '700', fontSize: 16 },
  addForm: {
    backgroundColor: COLORS.surface, borderRadius: RADIUS.xl,
    padding: SPACING.md, marginBottom: SPACING.md, ...SHADOWS.card,
  },
  addFormTitle: { fontSize: 17, fontWeight: '700', color: COLORS.textPrimary, marginBottom: 12 },
  label: { fontSize: 12, fontWeight: '600', color: COLORS.textSecondary, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  chipRow: { marginBottom: 16 },
  chip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 12, paddingVertical: 8, marginRight: 8,
    borderRadius: RADIUS.pill, borderWidth: 1.5, borderColor: COLORS.border,
    backgroundColor: COLORS.background,
  },
  chipActive: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  chipEmoji: { fontSize: 16 },
  chipText: { fontSize: 13, color: COLORS.textSecondary },
  chipTextActive: { color: COLORS.primary, fontWeight: '700' },
  marketChip: {
    paddingHorizontal: 12, paddingVertical: 8, marginRight: 8,
    borderRadius: RADIUS.pill, borderWidth: 1.5, borderColor: COLORS.border,
    backgroundColor: COLORS.background,
  },
  addFormBtns: { flexDirection: 'row', gap: 10, marginTop: 4 },
  cancelBtn: { flex: 1, borderWidth: 1.5, borderColor: COLORS.border, borderRadius: RADIUS.md, padding: 12, alignItems: 'center' },
  cancelBtnText: { color: COLORS.textSecondary, fontWeight: '600' },
  confirmBtn: { flex: 2, backgroundColor: COLORS.primary, borderRadius: RADIUS.md, padding: 12, alignItems: 'center' },
  confirmBtnText: { color: COLORS.white, fontWeight: '700' },
  saveBtn: {
    backgroundColor: COLORS.primary, borderRadius: RADIUS.lg,
    padding: SPACING.md, alignItems: 'center',
    marginTop: SPACING.md, ...SHADOWS.card,
  },
  btnDisabled: { opacity: 0.6 },
  saveBtnText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
});
