"""
Firebase Cloud Messaging — V1 API VERSION

Firebase deprecated Legacy API. We now use:
- Firebase Admin SDK with V1 API (already enabled in your project)
- This works with your existing firebase.json credentials file
- No server key needed — uses service account authentication
"""

import json
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional, Dict

from app.config import settings


class FirebaseService:

    def __init__(self):
        self._initialized = False
        self._init_firebase()

    def _init_firebase(self):
        try:
            if firebase_admin._apps:
                self._initialized = True
                return

            if settings.FIREBASE_CREDENTIALS_JSON:
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
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
            print(f"⚠️  Firebase not initialized: {e}")
            self._initialized = False

    def _is_expo_token(self, token: str) -> bool:
        return token.startswith('ExponentPushToken[')

    async def _send_via_expo(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """Send via Expo Push API for Expo tokens."""
        import httpx
        try:
            payload = {
                "to": token,
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
                "priority": "high",
                "channelId": "kisaan-mitra",
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip, deflate",
                        "Content-Type": "application/json",
                    }
                )
                result = response.json()

            ticket = result.get("data", {})
            if ticket.get("status") == "ok":
                print(f"✅ Expo push sent! ID: {ticket.get('id')}")
                return True
            else:
                err = ticket.get("message", result)
                print(f"❌ Expo push failed: {err}")
                return False

        except Exception as e:
            print(f"❌ Expo push error: {e}")
            return False

    async def _send_via_firebase_v1(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "normal",
    ) -> bool:
        """Send via Firebase Admin SDK V1 API."""
        if not self._initialized:
            print("⚠️  Firebase not initialized")
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                android=messaging.AndroidConfig(
                    priority="high" if priority == "high" else "normal",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="kisaan-mitra",
                        priority="high" if priority == "high" else "default",
                    ),
                ),
            )
            response = messaging.send(message)
            print(f"✅ Firebase V1 push sent: {response}")
            return True

        except messaging.UnregisteredError:
            print("⚠️  FCM token expired — user needs to re-login")
            return False
        except Exception as e:
            print(f"❌ Firebase send error: {e}")
            return False

    async def send_price_alert(
        self,
        fcm_token: Optional[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        priority: str = "normal",
    ) -> bool:
        """
        Send push notification.
        Automatically picks correct method based on token type:
        - ExponentPushToken[...] → Expo Push API
        - FCM token → Firebase V1 API
        """
        if not fcm_token:
            print("⚠️  No push token")
            return False

        if self._is_expo_token(fcm_token):
            print(f"📱 Sending via Expo Push API")
            return await self._send_via_expo(fcm_token, title, body, data)
        else:
            print(f"📱 Sending via Firebase V1 API")
            return await self._send_via_firebase_v1(
                fcm_token, title, body, data, priority
            )


firebase_service = FirebaseService()