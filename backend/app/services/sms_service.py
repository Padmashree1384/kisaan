"""
Fast2SMS integration for sending SMS alerts to farmers.

Docs: https://docs.fast2sms.com/
Supports: DLT-registered transactional and promotional routes.
"""

import httpx
from typing import Optional, List

from app.config import settings


class SMSService:
    """
    Send SMS using Fast2SMS Bulk API.
    Uses the DLT transactional route for reliability.
    """

    def __init__(self):
        self.api_key = settings.FAST2SMS_API_KEY
        self.sender_id = settings.FAST2SMS_SENDER_ID
        self.base_url = settings.FAST2SMS_BASE_URL

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "")

    async def send_sms(
        self,
        phone: str,
        message: str,
        priority: str = "Normal",
    ) -> bool:
        """
        Send a single SMS to a farmer's phone number.

        Args:
            phone: 10-digit Indian mobile number (no country code)
            message: SMS body (max 160 chars for single SMS)
            priority: "Normal" or "High"

        Returns:
            True if API accepted the message, False otherwise
        """
        if not self._is_configured():
            print(f"⚠️  Fast2SMS not configured — would send to {phone}: {message}")
            return False  # Graceful dev fallback

        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        payload = {
            "route": "dlt",           # DLT transactional route
            "sender_id": self.sender_id,
            "message": message,
            "variables_values": "",
            "flash": "0",
            "numbers": phone,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                )
                data = response.json()

            if data.get("return") is True:
                print(f"✅ SMS sent to {phone}: {message[:50]}...")
                return True
            else:
                print(f"❌ SMS failed to {phone}: {data.get('message', 'Unknown error')}")
                return False

        except httpx.TimeoutException:
            print(f"⏱️  SMS timeout for {phone}")
            return False
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False

    async def send_bulk_sms(
        self,
        phones: List[str],
        message: str,
    ) -> int:
        """
        Send the same SMS to multiple numbers.
        Fast2SMS supports comma-separated numbers in one API call.
        Returns count of accepted requests (not guaranteed deliveries).
        """
        if not self._is_configured() or not phones:
            return 0

        # Fast2SMS accepts comma-separated numbers (max ~100 per call)
        numbers_str = ",".join(phones[:100])

        success = await self.send_sms(numbers_str, message)
        return len(phones) if success else 0

    # ── Pre-built message templates ─────────────────────────────────────────

    def build_price_alert_message(
        self,
        crop: str,
        market: str,
        price: float,
        change_pct: float,
        language: str = "en",
    ) -> str:
        """
        Build a concise, farmer-friendly SMS message.
        """
        direction = "upar" if change_pct > 0 else "neeche"
        change_str = f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%"

        if language == "kn":
            # Kannada message
            return (
                f"ಕಿಸಾನ್ ಮಿತ್ರ: {crop} ಬೆಲೆ {market} ನಲ್ಲಿ "
                f"₹{price:.0f}/ಕ್ವಿಂ ({change_str}). "
                f"ಈಗಲೇ ಮಾರಾಟ ಮಾಡಿ! - KISAAN"
            )
        else:
            # English (default)
            return (
                f"Kisaan Mitra Alert: {crop} price at {market} is "
                f"Rs.{price:.0f}/qtl ({change_str}). "
                f"Check app for details. -KISAAN"
            )

    def build_critical_alert_message(
        self,
        crop: str,
        market: str,
        price: float,
        language: str = "en",
    ) -> str:
        """Build an urgent critical-price SMS."""
        if language == "kn":
            return (
                f"🚨 ಜರೂರಿ! {crop} ₹{price:.0f}/ಕ್ವಿಂ "
                f"{market} ನಲ್ಲಿ - 7 ದಿನಗಳಲ್ಲಿ ಅತ್ಯಧಿಕ ಬೆಲೆ! "
                f"ಈಗಲೇ ಮಾರಾಟ ಮಾಡಿ. -KISAAN"
            )
        else:
            return (
                f"URGENT - Kisaan Mitra: {crop} at Rs.{price:.0f}/qtl "
                f"in {market} - HIGHEST PRICE in 7 days! "
                f"Sell NOW. -KISAAN"
            )

    def build_inactive_reminder_message(
        self,
        name: str,
        language: str = "en",
    ) -> str:
        """Re-engagement SMS for inactive users."""
        if language == "kn":
            return (
                f"ನಮಸ್ಕಾರ {name}! ಕಿಸಾನ್ ಮಿತ್ರ ಆಪ್ ತೆರೆಯಿರಿ - "
                f"ನಿಮ್ಮ ಬೆಳೆಗಳ ಹೊಸ ಬೆಲೆಗಳು ಕಾಯುತ್ತಿವೆ. -KISAAN"
            )
        else:
            return (
                f"Hello {name}! Open Kisaan Mitra app - "
                f"New mandi prices are waiting for your crops. "
                f"Don't miss out! -KISAAN"
            )


# Singleton instance
sms_service = SMSService()
