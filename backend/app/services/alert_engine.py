"""
Alert Engine — FIXED VERSION

WHAT CHANGED:
1. _find_affected_users() now matches on commodity + state only (NOT market/district)
   — This is the critical fix. AgMarket returns "Bangalore Urban" but users save "Bengaluru".
   — Strict 4-field matching was causing 0 users to be found → 0 notifications.

2. Added null checks for fcm_token and phone before dispatching.

3. Added proper logging so you can see exactly what's happening.

Alert decision table:
  Normal update  (< 10% change)  → Firebase push only
  Big jump       (≥ 10% change)  → Firebase push + SMS
  Critical       (≥ 15% OR 7-day high) → High priority Firebase + SMS
  Inactive user  (3+ days idle)  → SMS only
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.models.schemas import AlertType
from app.services.firebase_service import firebase_service
from app.services.sms_service import sms_service
from app.utils.database import get_db
from app.config import settings


class AlertEngine:

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
        1. Calculates % change
        2. Classifies alert type
        3. Finds affected users
        4. Dispatches notifications
        """
        if previous_price is None or previous_price == 0:
            print(f"⏭️  No previous price for {commodity} @ {market} — skipping alert")
            return

        change_pct = ((current_price - previous_price) / previous_price) * 100

        alert_type = await self._classify_alert(
            commodity=commodity,
            market=market,
            current_price=current_price,
            change_pct=change_pct,
        )

        # FIXED: match only on commodity + state, not market/district
        # because AgMarket returns "Bangalore Urban" but users type "Bengaluru"
        affected_users = await self._find_affected_users(commodity, state)

        if not affected_users:
            print(f"ℹ️  No users watching {commodity} in {state} — no alerts sent")
            return

        print(
            f"📢 [{alert_type.value.upper()}] {commodity} @ {market}: "
            f"₹{current_price:.0f} ({change_pct:+.1f}%) → notifying {len(affected_users)} users"
        )

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

        # Check for inactive users and send re-engagement SMS
        await self._process_inactive_reminders()

    async def _classify_alert(
        self,
        commodity: str,
        market: str,
        current_price: float,
        change_pct: float,
    ) -> AlertType:
        """Classify alert based on price change magnitude and 7-day history."""
        abs_change = abs(change_pct)

        # 15%+ change = Critical
        if abs_change >= settings.CRITICAL_THRESHOLD * 100:
            return AlertType.CRITICAL

        # Price rising AND is the 7-day high = Critical
        if change_pct > 0 and await self._is_7day_high(commodity, market, current_price):
            return AlertType.CRITICAL

        # 10%+ change = Big Jump (Firebase + SMS)
        if abs_change >= settings.BIG_JUMP_THRESHOLD * 100:
            return AlertType.BIG_JUMP

        # Anything else = Normal (Firebase push only)
        return AlertType.NORMAL

    async def _is_7day_high(
        self,
        commodity: str,
        market: str,
        current_price: float,
    ) -> bool:
        """Returns True if current_price is the highest price in the last 7 days."""
        db = get_db()
        since = datetime.utcnow() - timedelta(days=7)

        # If no record exists with a HIGHER price in last 7 days, this IS the 7-day high
        higher_record = await db.prices.find_one(
            {
                "commodity": {"$regex": f"^{re.escape(commodity)}$", "$options": "i"},
                "market": {"$regex": f"^{re.escape(market)}$", "$options": "i"},
                "fetched_at": {"$gte": since},
                "modal_price": {"$gt": current_price},
            }
        )
        return higher_record is None

    async def _find_affected_users(
        self,
        commodity: str,
        state: str,
    ):
        """
        FIXED: Find users who are watching this commodity in this state.

        WHY only commodity + state:
        - User saves: market="Bengaluru", district="Bengaluru"
        - AgMarket returns: market="Yeshwanthpur", district="Bangalore Urban"
        - Strict matching → 0 users found → 0 notifications
        - Loose matching on commodity+state → correct users found → notifications work

        Users will get price alerts for their watched commodity from any mandi
        in their state, which is actually more useful for farmers.
        """
        db = get_db()

        cursor = db.users.find(
            {
                "is_active": True,
                "crops": {
                    "$elemMatch": {
                        "commodity": {
                            "$regex": f"^{re.escape(commodity)}$",
                            "$options": "i",
                        },
                        "state": {
                            "$regex": f"^{re.escape(state)}$",
                            "$options": "i",
                        },
                        "alert_enabled": True,
                    }
                },
            }
        )

        users = await cursor.to_list(length=None)
        print(f"🔍 Found {len(users)} users watching {commodity} in {state}")
        return users

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
        """Send notification to a single user and save the record to DB."""
        db = get_db()

        language = user.get("language", "en")
        fcm_token = user.get("fcm_token")  # May be None if user hasn't enabled push
        phone = user.get("phone")

        # Build message content
        if alert_type == AlertType.CRITICAL:
            title = (
                "Urgent Price Alert!"
                if language == "en"
                else "ತುರ್ತು ಬೆಲೆ ಎಚ್ಚರಿಕೆ!"
            )
            body_en = sms_service.build_critical_alert_message(commodity, market, current_price, "en")
            body_kn = sms_service.build_critical_alert_message(commodity, market, current_price, "kn")
        else:
            direction = "increased" if change_pct > 0 else "decreased"
            title = f"{commodity} price {direction}"
            body_en = sms_service.build_price_alert_message(commodity, market, current_price, change_pct, "en")
            body_kn = sms_service.build_price_alert_message(commodity, market, current_price, change_pct, "kn")

        push_body = body_kn if language == "kn" else body_en
        sms_message = push_body

        push_data = {
            "alert_type": alert_type.value,
            "commodity": commodity,
            "market": market,
            "price": str(current_price),
            "change_pct": f"{change_pct:.2f}",
        }

        firebase_sent = False
        sms_sent = False

        if alert_type == AlertType.NORMAL:
            if fcm_token:
                firebase_sent = await firebase_service.send_price_alert(
                    fcm_token, title, push_body, push_data
                )
            else:
                print(f"  ⚠️  No FCM token for user {user.get('name')} — push skipped")

        elif alert_type == AlertType.BIG_JUMP:
            if fcm_token:
                firebase_sent = await firebase_service.send_price_alert(
                    fcm_token, title, push_body, push_data, priority="high"
                )
            if phone:
                sms_sent = await sms_service.send_sms(phone, sms_message)

        elif alert_type == AlertType.CRITICAL:
            if fcm_token:
                firebase_sent = await firebase_service.send_price_alert(
                    fcm_token, title, push_body, push_data, priority="high"
                )
            if phone:
                sms_sent = await sms_service.send_sms(phone, sms_message, priority="High")

        # Always save the notification record — even if delivery failed
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

        result = await db.notifications.insert_one(notification_doc)
        print(
            f"  ✅ Notification saved: {user.get('name')} | "
            f"push={'yes' if firebase_sent else 'no'} | "
            f"sms={'yes' if sms_sent else 'no'}"
        )

    async def _process_inactive_reminders(self):
        """Send SMS re-engagement to users who haven't used the app in 3+ days."""
        db = get_db()

        inactive_since = datetime.utcnow() - timedelta(days=settings.INACTIVE_DAYS_THRESHOLD)
        reminder_cooldown = datetime.utcnow() - timedelta(days=3)

        cursor = db.users.find({
            "is_active": True,
            "phone": {"$exists": True, "$ne": None},
            "last_active": {"$lt": inactive_since},
        })
        inactive_users = await cursor.to_list(length=200)

        sent_count = 0
        for user in inactive_users:
            user_id = str(user["_id"])

            # Don't spam — only one reminder per 3 days
            recent_reminder = await db.notifications.find_one({
                "user_id": user_id,
                "alert_type": AlertType.INACTIVE.value,
                "created_at": {"$gte": reminder_cooldown},
            })
            if recent_reminder:
                continue

            language = user.get("language", "en")
            message = sms_service.build_inactive_reminder_message(user.get("name", "Farmer"), language)
            sms_sent = await sms_service.send_sms(user["phone"], message)

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
            sent_count += 1

        if sent_count > 0:
            print(f"📱 Sent {sent_count} inactive user reminders")


# Singleton
alert_engine = AlertEngine()