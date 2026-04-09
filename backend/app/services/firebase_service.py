def _init_firebase(self):
    """Initialize Firebase Admin SDK once."""
    try:
        if firebase_admin._apps:
            self._initialized = True
            return

        if settings.FIREBASE_CREDENTIALS_JSON:
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            from firebase_admin import credentials
            cred = credentials.Certificate(cred_dict)
        else:
            import os
            path = settings.FIREBASE_CREDENTIALS_PATH
            abs_path = os.path.abspath(path)
            print(f"🔍 Loading Firebase from: {abs_path}")
            cred = credentials.Certificate(abs_path)

        firebase_admin.initialize_app(cred)
        self._initialized = True
        print("✅ Firebase Admin SDK initialized")

    except Exception as e:
        print(f"⚠️  Firebase not initialized: {e}. Push notifications disabled.")
        self._initialized = False