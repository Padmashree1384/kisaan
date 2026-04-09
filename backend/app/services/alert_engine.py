"""
Alert Engine — the core intelligence of Kisaan Mitra.

Decision logic:
  ┌──────────────────────┬──────────────────────────────────────┐
  │ Situation            │ Action                               │
  ├──────────────────────┼──────────────────────────────────────┤
  │ Normal update        │ Firebase push only                   │
  │ Big jump (>10%)      │ Firebase push + SMS                  │
  │ Critical (>15% OR    │ Firebase push + SMS (high priority)  │
  │   7-day high)        │                                      │
  │ User inactive 3d+    │ SMS only (re-engagement)             │
  └──────────────────────┴──────────────────────────────────────┘
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.models.schemas import AlertType
from app.services.firebase_service import firebase_service
from app.services.sms_service import sms_service
from app.utils.database import get_db
from app.config import settings


class AlertEngine:
    """
    Evaluates price changes and dispatches notifications
    via the appropriate channel(s).
    """

    async def process_price_update(
        self,
        commodity: str,
        market: str,
        state: str,
        district: str,
        current_price: float,
        previous_price: Optional[float],
    ):
        """
        Main entry point called by the scheduler for each price update.
        Determines alert type and notifies affected users.
        """
        if previous_price is None or previous_price == 0:
            # First time seeing this commodity — no comparison possible yet
            return

        change_pct = ((current_price - previous_price) / previous_price) * 100

        # Determine alert type
        alert_type = await self._classify_alert(
            commodity=commodity,
            market=market,
            current_price=current_price,
            change_pct=change_pct,
        )

        # Find all users watching this crop+mandi
        affected_users = await self._find_affected_users(commodity, state, district, market)

        if not affected_users:
            return

        print(
            f"📢 Alert [{alert_type}] {commodity} @ {market}: "
            f"₹{current_price} ({change_pct:+.1f}%) → {len(affected_users)} users"
        )

        # Build messages for each user and dispatch
        for user in affected_users:
            await self._dispatch_alert(
                user=user,
                alert_type=alert_type,
                commodity=commodity,
                market=market,
                current_price=current_price,
                previous_price=previous_price,
                change_pct=change_pct,
            )

        # Send inactive user reminders (separate cadence)
        await self._process_inactive_reminders()

    async def _classify_alert(
        self,
        commodity: str,
        market: str,
        current_price: float,
        change_pct: float,
    ) -> AlertType:
        """
        Classify the alert type based on price change and history.
        """
        abs_change = abs(change_pct)

        # Critical: exceeds critical threshold OR is highest in last 7 days
        if abs_change >= settings.CRITICAL_THRESHOLD * 100:
            return AlertType.CRITICAL

        # Check if current price is the 7-day high (critical condition)
        if change_pct > 0 and await self._is_7day_high(commodity, market, current_price):
            return AlertType.CRITICAL

        # Big jump: exceeds big-jump threshold
        if abs_change >= settings.BIG_JUMP_THRESHOLD * 100:
            return AlertType.BIG_JUMP

        # Normal update: small or no change
        return AlertType.NORMAL

    async def _is_7day_high(
        self,
        commodity: str,
        market: str,
        current_price: float,
    ) -> bool:
        """
        Check if current_price is the highest modal price in the last 7 days.
        """
        db = get_db()
        since = datetime.utcnow() - timedelta(days=7)
        result = await db.prices.find_one(
            {
                "commodity": {"$regex": commodity, "$options": "i"},
                "market": {"$regex": market, "$options": "i"},
                "fetched_at": {"$gte": since},
                "modal_price": {"$gt": current_price},
            },
            sort=[("modal_price", -1)],
        )
        return result is None  # No record with a higher price found → it's the 7-day high

    async def _find_affected_users(
        self,
        commodity: str,
        state: str,
        district: str,
        market: str,
    ):
        """
        Find all active users who have this crop+location in their watchlist
        and have alert_enabled = True.
        """
        db = get_db()
        cursor = db.users.find({
            "is_active": True,
            "crops": {
                "$elemMatch": {
                    "commodity": {"$regex": commodity, "$options": "i"},
                    "alert_enabled": True,
                    # Match state broadly — users track by district
                    "$or": [
                        {"district": {"$regex": district, "$options": "i"}},
                        {"state": {"$regex": state, "$options": "i"}},
                    ],
                }
            },
        })
        return await cursor.to_list(length=1000)

    async def _dispatch_alert(
        self,
        user: Dict[str, Any],
        alert_type: AlertType,
        commodity: str,
        market: str,
        current_price: float,
        previous_price: float,
        change_pct: float,
    ):
        """
        Send notifications to a single user based on alert type.
        Stores notification record in DB.
        """
        db = get_db()
        language = user.get("language", "en")
        fcm_token = user.get("fcm_token")
        phone = user.get("phone")

        # Build messages
        if alert_type == AlertType.CRITICAL:
            title = "🚨 Urgent Price Alert!" if language == "en" else "🚨 ತುರ್ತು ಬೆಲೆ ಎಚ್ಚರಿಕೆ!"
            body_en = sms_service.build_critical_alert_message(commodity, market, current_price, "en")
            body_kn = sms_service.build_critical_alert_message(commodity, market, current_price, "kn")
            sms_message = body_kn if language == "kn" else body_en
        else:
            direction = "increased" if change_pct > 0 else "decreased"
            title = f"💰 {commodity} Price {direction.title()}"
            body_en = sms_service.build_price_alert_message(commodity, market, current_price, change_pct, "en")
            body_kn = sms_service.build_price_alert_message(commodity, market, current_price, change_pct, "kn")
            sms_message = body_kn if language == "kn" else body_en

        push_body = body_kn if language == "kn" else body_en
        push_data = {
            "alert_type": alert_type.value,
            "commodity": commodity,
            "market": market,
            "price": str(current_price),
            "change_pct": f"{change_pct:.2f}",
        }

        firebase_sent = False
        sms_sent = False

        # ── Dispatch based on alert type ────────────────────────────────────
        if alert_type == AlertType.NORMAL:
            # Firebase only
            firebase_sent = await firebase_service.send_price_alert(
                fcm_token, title, push_body, push_data
            )

        elif alert_type == AlertType.BIG_JUMP:
            # Firebase + SMS
            firebase_sent = await firebase_service.send_price_alert(
                fcm_token, title, push_body, push_data, priority="high"
            )
            sms_sent = await sms_service.send_sms(phone, sms_message)

        elif alert_type == AlertType.CRITICAL:
            # Firebase + SMS (high priority)
            firebase_sent = await firebase_service.send_price_alert(
                fcm_token, title, push_body, push_data, priority="high"
            )
            sms_sent = await sms_service.send_sms(phone, sms_message, priority="High")

        # ── Store notification record ────────────────────────────────────────
        notification_doc = {
            "user_id": str(user["_id"]),
            "alert_type": alert_type.value,
            "commodity": commodity,
            "market": market,
            "old_price": previous_price,
            "new_price": current_price,
            "change_pct": round(change_pct, 2),
            "message_en": body_en,
            "message_kn": body_kn,
            "firebase_sent": firebase_sent,
            "sms_sent": sms_sent,
            "status": "sent" if (firebase_sent or sms_sent) else "failed",
            "created_at": datetime.utcnow(),
        }
        await db.notifications.insert_one(notification_doc)

    async def _process_inactive_reminders(self):
        """
        Find users who haven't opened the app in N days and send SMS reminders.
        Runs as part of the scheduled cycle.
        """
        db = get_db()
        inactive_since = datetime.utcnow() - timedelta(days=settings.INACTIVE_DAYS_THRESHOLD)

        # Only send one reminder every 3 days — check last notification
        cursor = db.users.find({
            "is_active": True,
            "phone": {"$exists": True, "$ne": None},
            "last_active": {"$lt": inactive_since},
        })
        inactive_users = await cursor.to_list(length=200)

        for user in inactive_users:
            user_id = str(user["_id"])
            # Check if we already sent a reminder in the last 3 days
            recent_reminder = await db.notifications.find_one({
                "user_id": user_id,
                "alert_type": AlertType.INACTIVE.value,
                "created_at": {"$gte": inactive_since},
            })
            if recent_reminder:
                continue  # Already reminded recently

            language = user.get("language", "en")
            message = sms_service.build_inactive_reminder_message(user["name"], language)
            sms_sent = await sms_service.send_sms(user["phone"], message)

            # Log the reminder
            await db.notifications.insert_one({
                "user_id": user_id,
                "alert_type": AlertType.INACTIVE.value,
                "commodity": "",
                "market": "",
                "old_price": 0,
                "new_price": 0,
                "change_pct": 0,
                "message_en": message,
                "message_kn": "",
                "firebase_sent": False,
                "sms_sent": sms_sent,
                "status": "sent" if sms_sent else "failed",
                "created_at": datetime.utcnow(),
            })

        if inactive_users:
            print(f"📱 Sent {len(inactive_users)} inactive user reminders")


# Singleton instance
alert_engine = AlertEngine()
