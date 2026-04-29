/**
 * Kisaan Mitra — Design System
 * Earthy greens, warm ambers, clean whites.
 * Farmer-friendly: large text, high contrast, simple icons.
 */

export const COLORS = {
  // Primary greens
  primary:        '#2D7A45',   // Main brand green
  primaryDark:    '#1B5E20',   // Deep forest green
  primaryLight:   '#E8F5EC',   // Pale green background
  primaryMid:     '#4CAF6F',   // Medium green for accents

  // Alert colors
  success:        '#2D7A45',
  warning:        '#E8901A',   // Amber — price movement
  warningLight:   '#FFF3E0',
  danger:         '#C62828',   // Red — critical alert
  dangerLight:    '#FFEBEE',
  info:           '#1565C0',
  infoLight:      '#E3F2FD',

  // Neutrals
  white:          '#FFFFFF',
  background:     '#F5F7F5',   // Slightly green-tinted page bg
  surface:        '#FFFFFF',   // Card surfaces
  border:         '#E0E4E0',
  divider:        '#F0F2F0',

  // Text
  textPrimary:    '#1A2E1A',   // Dark green-black
  textSecondary:  '#5D6B5D',   // Muted green-grey
  textHint:       '#9E9E9E',
  textOnGreen:    '#FFFFFF',

  // Crop icon backgrounds
  tomatoBg:       '#FFEBE5',
  onionBg:        '#F3E5F5',
  potatoBg:       '#FFF8E1',
  riceBg:         '#E8F5E9',
  maizeBg:        '#FFFDE7',
  groundnutBg:    '#FBE9E7',
};

export const TYPOGRAPHY = {
  // Font sizes — larger for farmer-friendliness
  h1:   { fontSize: 28, fontWeight: '700', lineHeight: 36 },
  h2:   { fontSize: 22, fontWeight: '700', lineHeight: 30 },
  h3:   { fontSize: 18, fontWeight: '600', lineHeight: 26 },
  h4:   { fontSize: 16, fontWeight: '600', lineHeight: 22 },
  body: { fontSize: 15, fontWeight: '400', lineHeight: 22 },
  bodySmall: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
  caption: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
  label: { fontSize: 11, fontWeight: '600', letterSpacing: 0.5 },

  // Price display — big and bold
  priceXL: { fontSize: 36, fontWeight: '800', lineHeight: 44 },
  priceLG: { fontSize: 24, fontWeight: '700', lineHeight: 30 },
  priceMD: { fontSize: 18, fontWeight: '700', lineHeight: 24 },
};

export const SPACING = {
  xs:  4,
  sm:  8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const RADIUS = {
  sm:  8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 999,
};

export const SHADOWS = {
 card: {
  // ✅ Mobile
  shadowColor: "#000",
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.1,
  shadowRadius: 4,
  elevation: 3,

  // ✅ Web fix
  boxShadow: "0px 4px 10px rgba(0,0,0,0.1)",
},
  elevated: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10,
    shadowRadius: 16,
    elevation: 6,
  },
};

/** Map crop names to emoji and background colors */
export const CROP_META: Record<string, { emoji: string; bg: string }> = {
  Tomato:     { emoji: '🍅', bg: COLORS.tomatoBg },
  Onion:      { emoji: '🧅', bg: COLORS.onionBg },
  Potato:     { emoji: '🥔', bg: COLORS.potatoBg },
  Rice:       { emoji: '🌾', bg: COLORS.riceBg },
  Paddy:      { emoji: '🌾', bg: COLORS.riceBg },
  Maize:      { emoji: '🌽', bg: COLORS.maizeBg },
  Wheat:      { emoji: '🌾', bg: COLORS.riceBg },
  Groundnut:  { emoji: '🥜', bg: COLORS.groundnutBg },
  Soyabean:   { emoji: '🫘', bg: COLORS.potatoBg },
  default:    { emoji: '🌿', bg: COLORS.primaryLight },
};

export function getCropMeta(commodity: string) {
  return CROP_META[commodity] ?? CROP_META.default;
}

/** Format price for display */
export function formatPrice(price: number): string {
  return `₹${price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

/** Format percentage change */
export function formatChange(pct: number | null | undefined): string {
  if (pct === null || pct === undefined) return '—';
  const sign = pct > 0 ? '+' : '';
  return `${sign}${pct.toFixed(1)}%`;
}

/** Get color for a change percentage */
export function changeColor(pct: number | null | undefined): string {
  if (!pct) return COLORS.textHint;
  if (pct > 0) return COLORS.success;
  return COLORS.danger;
}

/** Get alert badge color */
export function alertColor(alertType: string): string {
  switch (alertType) {
    case 'critical':  return COLORS.danger;
    case 'big_jump':  return COLORS.warning;
    case 'inactive':  return COLORS.info;
    default:          return COLORS.primary;
  }
}
