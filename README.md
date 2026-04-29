# 🌾 Kisaan Mitra — Smart Farmer Assistant

A production-ready full-stack mobile application that sends real-time mandi price alerts to Indian farmers via push notifications (Firebase) and SMS (Fast2SMS).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    React Native (Expo)                       │
│      Splash → Login/Register → Dashboard → Alerts           │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API (JWT Auth)
┌───────────────────────▼─────────────────────────────────────┐
│                   FastAPI Backend                            │
│   /register  /login  /prices  /notifications  /preferences  │
└──────┬──────────────┬────────────────┬──────────────────────┘
       │              │                │
  ┌────▼────┐   ┌─────▼──────┐  ┌─────▼──────┐
  │ MongoDB │   │  Firebase  │  │  Fast2SMS  │
  │(Motor)  │   │    FCM     │  │    SMS     │
  └─────────┘   └────────────┘  └────────────┘
       ▲
  ┌────┴────────────┐
  │ APScheduler     │  ← Runs every 30 mins
  │ AgMarket API    │  ← data.gov.in prices
  └─────────────────┘
```

## 📢 Alert Decision Matrix

| Situation | Firebase Push | SMS |
|-----------|:---:|:---:|
| Normal price update | ✅ | ❌ |
| Price jump ≥ 10% | ✅ | ✅ |
| Critical alert ≥ 15% or 7-day high | ✅ | ✅ (High Priority) |
| User inactive 3+ days | ❌ | ✅ |

---

## 📁 Project Structure

```
kisaan-mitra/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Settings & env vars
│   │   ├── api/
│   │   │   ├── auth.py              # POST /register, /login
│   │   │   ├── prices.py            # GET /prices, /trending
│   │   │   ├── notifications.py     # GET /notifications
│   │   │   └── users.py             # POST /user/preferences
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models (User, Price, Notification)
│   │   ├── services/
│   │   │   ├── agmarket_service.py  # AgMarket API wrapper
│   │   │   ├── firebase_service.py  # Firebase FCM
│   │   │   ├── sms_service.py       # Fast2SMS integration
│   │   │   └── alert_engine.py      # Core alert decision logic
│   │   ├── scheduler/
│   │   │   └── price_scheduler.py   # APScheduler jobs
│   │   └── utils/
│   │       └── database.py          # Motor MongoDB connection
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── App.tsx                      # Navigation root
    ├── app.json                     # Expo config
    ├── package.json
    └── src/
        ├── screens/
        │   ├── SplashScreen.tsx
        │   ├── LoginScreen.tsx
        │   ├── RegisterScreen.tsx
        │   ├── HomeScreen.tsx       # Dashboard with live prices
        │   ├── CropSelectionScreen.tsx
        │   ├── NotificationsScreen.tsx
        │   └── ProfileScreen.tsx
        ├── services/
        │   ├── api.ts               # Axios API client
        │   └── AuthContext.tsx      # Global auth state
        ├── i18n/
        │   └── translations.ts      # English + Kannada strings
        └── utils/
            └── theme.ts             # Colors, typography, helpers
```

---

## ⚙️ Backend Setup

### Prerequisites
- Python 3.10+
- MongoDB (local or MongoDB Atlas)
- Firebase project with service account
- Fast2SMS account
- data.gov.in API key

### Step 1: Install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=kisaan_mitra
SECRET_KEY=your-secret-key-here

# Firebase — download from Firebase Console > Project Settings > Service Accounts
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json

# Fast2SMS — get from https://www.fast2sms.com/dashboard
FAST2SMS_API_KEY=your_key_here
FAST2SMS_SENDER_ID=KISAAN

# AgMarket — register at https://data.gov.in and generate API key
AGMARKET_API_KEY=your_key_here
```

### Step 3: Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project (e.g. "kisaan-mitra")
3. Enable **Cloud Messaging** (FCM)
4. Go to **Project Settings > Service Accounts**
5. Click **Generate new private key** → download JSON
6. Save it as `backend/firebase-credentials.json`

### Step 4: Run the server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: **http://localhost:8000/docs**

---

## 📱 Frontend Setup

### Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g expo`
- Android emulator or physical device

### Step 1: Install dependencies

```bash
cd frontend
npm install
```

### Step 2: Configure API URL

Edit `src/services/api.ts` and set your backend URL:

```typescript
// For Android emulator
const BASE_URL = 'http://10.0.2.2:8000/api/v1';

// For physical device (use your machine's local IP)
const BASE_URL = 'http://192.168.1.x:8000/api/v1';

// For production
const BASE_URL = 'https://your-api.com/api/v1';
```

### Step 3: Firebase React Native Setup

1. In Firebase Console, add an **Android** app
   - Package name: `com.kisaanmitra.app`
   - Download `google-services.json`
   - Place at `frontend/android/app/google-services.json`

2. For iOS, add an **iOS** app
   - Bundle ID: `com.kisaanmitra.app`
   - Download `GoogleService-Info.plist`
   - Place at `frontend/ios/KisaanMitra/GoogleService-Info.plist`

### Step 4: Run the app

```bash
cd frontend
npx expo start

# Press 'a' for Android emulator
# Press 'i' for iOS simulator
# Scan QR code with Expo Go app for physical device
```

---

## 🗄️ MongoDB Schema Design

### `users` collection
```json
{
  "_id": "ObjectId",
  "name": "Ramesh Kumar",
  "phone": "9876543210",
  "hashed_password": "bcrypt_hash",
  "location_state": "Karnataka",
  "location_district": "Bengaluru",
  "language": "en",
  "crops": [
    {
      "commodity": "Tomato",
      "state": "Karnataka",
      "district": "Bengaluru",
      "market": "Bengaluru",
      "alert_enabled": true
    }
  ],
  "fcm_token": "Firebase_device_token",
  "is_active": true,
  "last_active": "ISODate",
  "created_at": "ISODate"
}
```

### `prices` collection
```json
{
  "_id": "ObjectId",
  "state": "Karnataka",
  "district": "Bengaluru",
  "market": "Bengaluru",
  "commodity": "Tomato",
  "variety": "Local",
  "arrival_date": "01/07/2025",
  "min_price": 3000.0,
  "max_price": 4800.0,
  "modal_price": 4200.0,
  "fetched_at": "ISODate"
}
```

### `notifications` collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId_ref",
  "alert_type": "critical",
  "commodity": "Tomato",
  "market": "Bengaluru",
  "old_price": 3040.0,
  "new_price": 4200.0,
  "change_pct": 38.15,
  "message_en": "URGENT - Tomato at Rs.4200/qtl...",
  "message_kn": "ತುರ್ತು - ಟಮ್ಯಾಟೋ ₹4200...",
  "firebase_sent": true,
  "sms_sent": true,
  "status": "sent",
  "created_at": "ISODate"
}
```

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/register` | None | Register new farmer |
| POST | `/api/v1/login` | None | Login, get JWT |
| GET | `/api/v1/prices` | JWT | Get mandi prices |
| GET | `/api/v1/prices/trending` | JWT | Top price movers |
| GET | `/api/v1/prices/history` | JWT | 7-day price chart data |
| POST | `/api/v1/prices/refresh` | JWT | Manual price refresh |
| GET | `/api/v1/notifications` | JWT | Alert history |
| GET | `/api/v1/notifications/unread-count` | JWT | Badge count |
| POST | `/api/v1/user/preferences` | JWT | Update crop watchlist |
| GET | `/api/v1/user/profile` | JWT | Get user profile |
| PUT | `/api/v1/user/fcm-token` | JWT | Update FCM device token |

---

## 🔔 Fast2SMS Integration Notes

1. Register at [fast2sms.com](https://www.fast2sms.com)
2. Go to **Dev API** and copy your API key
3. For DLT transactional route, register your **Sender ID** and **message template** with TRAI
4. For testing (promotional route), no DLT registration needed

The SMS messages in `sms_service.py` must match your DLT-approved templates for production use.

---

## 🌐 AgMarket API Notes

1. Register at [data.gov.in](https://data.gov.in)
2. Go to [Agmarknet dataset](https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070)
3. Click **Get API** and copy your API key
4. The API updates daily — price data reflects previous day's market arrivals

---

## 🚀 Production Deployment

### Backend (e.g. Railway, Render, DigitalOcean)

```bash
# Dockerfile-friendly start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
# npx ngrok http 8000

### MongoDB
Use [MongoDB Atlas](https://www.mongodb.com/atlas) free tier. Replace `MONGODB_URL` with your Atlas connection string.

### Environment Variables
Set all `.env` values as secrets in your hosting platform. Never commit `.env` to git.

---

## 🎯 Features Summary

- ✅ JWT authentication (register + login)
- ✅ Live mandi prices from AgMarket API
- ✅ Smart alert routing (Firebase / SMS / both)
- ✅ APScheduler background price fetching every 30 min
- ✅ Notification history screen
- ✅ Multi-language: English + Kannada
- ✅ Crop watchlist management
- ✅ Inactive user re-engagement via SMS
- ✅ Pull-to-refresh dashboard
- ✅ Offline-friendly (AsyncStorage caching)
- ✅ Clean, farmer-friendly UI with large text and emojis

---

*Built for Indian farmers 🇮🇳 | Powered by AgMarket, Firebase & Fast2SMS*
