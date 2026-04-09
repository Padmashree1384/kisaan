import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, ActivityIndicator,
  KeyboardAvoidingView, Platform, StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../services/AuthContext';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../utils/theme';

const KARNATAKA_DISTRICTS = [
  'Bengaluru', 'Mysuru', 'Hubballi', 'Mangaluru', 'Belagavi',
  'Davanagere', 'Ballari', 'Vijayapura', 'Shivamogga', 'Tumakuru',
  'Raichur', 'Kalaburagi', 'Hassan', 'Udupi', 'Dharwad',
];

const STATES = ['Karnataka', 'Maharashtra', 'Andhra Pradesh'];

export default function RegisterScreen({ navigation }: any) {
  const { register } = useAuth();

  const [form, setForm] = useState({
    name: '',
    phone: '',
    password: '',
    location_state: 'Karnataka',
    location_district: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (key: string, value: string) => {
    setForm(f => ({ ...f, [key]: value }));
    setErrors(e => ({ ...e, [key]: '' }));
  };

  // ✅ VALIDATION
  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (form.name.trim().length < 2)
      newErrors.name = 'Name must be at least 2 characters';

    if (!/^[6-9]\d{9}$/.test(form.phone))
      newErrors.phone = 'Enter valid 10-digit mobile number';

    if (form.password.length < 4)
      newErrors.password = 'Password must be at least 4 characters';

    if (!form.location_district)
      newErrors.district = 'Please enter your district';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // ✅ REGISTER HANDLER (FIXED)
  const handleRegister = async () => {
    if (!validate()) return;

    // 🔥 CLEAN PHONE (IMPORTANT)
    const cleanPhone = form.phone.replace(/\D/g, '');

    if (cleanPhone.length !== 10) {
      Alert.alert("Invalid Number", "Enter valid 10-digit mobile number");
      return;
    }

    setLoading(true);

    try {
      await register({
        name: form.name.trim(),
        phone: cleanPhone, // ✅ FIXED
        password: form.password,
        location_state: form.location_state,
        location_district: form.location_district,
        language: 'en',
        crops: [],
      });

      Alert.alert("Success 🎉", "Account created successfully!");
      navigation.replace('MainTabs');

    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Registration failed. Please try again.';
      Alert.alert('Registration Failed', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primaryDark} />

      <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>

        <LinearGradient colors={[COLORS.primaryDark, COLORS.primary]} style={styles.header}>
          <Text style={styles.logo}>👨‍🌾</Text>
          <Text style={styles.headerTitle}>Create Account</Text>
          <Text style={styles.headerSubtitle}>Join thousands of smart farmers</Text>
        </LinearGradient>

        <View style={styles.card}>

          {/* NAME */}
          <Text style={styles.label}>Full Name</Text>
          <TextInput
            style={[styles.input, errors.name ? styles.inputError : undefined]}
            placeholder="Ramesh Kumar"
            value={form.name}
            onChangeText={(v) => update('name', v)}
          />
          {errors.name && <Text style={styles.errorText}>{errors.name}</Text>}

          {/* PHONE */}
          <Text style={styles.label}>Mobile Number</Text>
          <View style={[styles.phoneWrapper, errors.phone ? styles.inputError : undefined]}>
            <Text style={styles.phonePrefix}>+91</Text>
            <TextInput
              style={styles.phoneInput}
              placeholder="9876543210"
              keyboardType="number-pad"
              maxLength={10}
              value={form.phone}
              onChangeText={(v) => {
                const onlyNumbers = v.replace(/\D/g, '');
                update('phone', onlyNumbers);
              }}
            />
          </View>
          {errors.phone && <Text style={styles.errorText}>{errors.phone}</Text>}

          {/* PASSWORD */}
          <Text style={styles.label}>Password</Text>
          <TextInput
            style={[styles.input, errors.password ? styles.inputError : undefined]}
            placeholder="Min 4 characters"
            secureTextEntry
            value={form.password}
            onChangeText={(v) => update('password', v)}
          />
          {errors.password && <Text style={styles.errorText}>{errors.password}</Text>}

          {/* STATE */}
          <Text style={styles.label}>State</Text>
          <View style={styles.stateRow}>
            {STATES.map(s => (
              <TouchableOpacity
                key={s}
                style={[styles.stateChip, form.location_state === s && styles.stateChipActive]}
                onPress={() => update('location_state', s)}
              >
                <Text style={{ color: form.location_state === s ? 'green' : 'gray' }}>
                  {s}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* DISTRICT */}
          <Text style={styles.label}>District</Text>
          <TextInput
            style={[styles.input, errors.district ? styles.inputError : null]}
            placeholder="Bengaluru"
            value={form.location_district}
            onChangeText={(v) => update('location_district', v)}
          />
          {errors.district && <Text style={styles.errorText}>{errors.district}</Text>}

          {/* DISTRICT CHIPS */}
          <ScrollView horizontal>
            {KARNATAKA_DISTRICTS.map(d => (
              <TouchableOpacity
                key={d}
                style={styles.districtChip}
                onPress={() => update('location_district', d)}
              >
                <Text>{d}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* BUTTON */}
          <TouchableOpacity style={styles.btn} onPress={handleRegister}>
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.btnText}>Register 🌱</Text>
            }
          </TouchableOpacity>

        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { paddingBottom: 40 },

  header: { padding: 40, alignItems: 'center' },
  logo: { fontSize: 50 },
  headerTitle: { color: 'white', fontSize: 24, fontWeight: 'bold' },
  headerSubtitle: { color: 'white' },

  card: { padding: 20 },

  label: { marginTop: 10, fontWeight: '600' },

  input: {
    borderWidth: 1,
    padding: 10,
    borderRadius: 8,
    marginTop: 5,
  },

  inputError: { borderColor: 'red' },
  errorText: { color: 'red' },

  phoneWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
  },

  phonePrefix: { marginRight: 10 },
  phoneInput: { flex: 1 },

  stateRow: { flexDirection: 'row', gap: 10 },

  stateChip: {
    padding: 8,
    borderWidth: 1,
    borderRadius: 20,
  },

  stateChipActive: { backgroundColor: '#d4f5d4' },

  districtChip: {
    padding: 8,
    marginRight: 5,
    borderWidth: 1,
    borderRadius: 20,
  },

  btn: {
    backgroundColor: 'green',
    padding: 15,
    marginTop: 20,
    borderRadius: 10,
    alignItems: 'center',
  },

  btnText: { color: 'white', fontWeight: 'bold' },
});