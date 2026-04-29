"""
Fast2SMS integration — FIXED ROUTE

CHANGE: Using route "q" (Quick) instead of "dlt"
- "dlt" requires registered Sender ID and DLT template (needs approval)
- "q" route works immediately without any registration
- Perfect for development and testing
"""

import httpx
from typing import Optional, List
from app.config import settings


class SMSService:

    def __init__(self):
        self.api_key = settings.FAST2SMS_API_KEY
        self.base_url = "https://www.fast2sms.com/dev/bulkV2"

    def _is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() != "")

    async def send_sms(
        self,
        phone: str,
        message: str,
        priority: str = "Normal",
    ) -> bool:
        """Send SMS using Fast2SMS Quick route (no DLT registration needed)."""
        if not self._is_configured():
            print(f"⚠️  Fast2SMS not configured — SMS skipped for {phone}")
            return False

        # Clean phone number — remove spaces, dashes, country code
        clean_phone = phone.replace(" ", "").replace("-", "")
        if clean_phone.startswith("+91"):
            clean_phone = clean_phone[3:]
        if clean_phone.startswith("91") and len(clean_phone) == 12:
            clean_phone = clean_phone[2:]

        if len(clean_phone) != 10:
            print(f"❌ Invalid phone number: {phone}")
            return False

        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "route": "q",              # Quick route — no DLT needed
            "message": message[:160],  # SMS limit
            "language": "english",
            "flash": 0,
            "numbers": clean_phone,
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
                print(f"✅ SMS sent to {clean_phone}")
                return True
            else:
                err = data.get("message", data)
                print(f"❌ SMS failed to {clean_phone}: {err}")
                return False

        except httpx.TimeoutException:
            print(f"⏱️  SMS timeout for {clean_phone}")
            return False
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False

    async def send_bulk_sms(self, phones: List[str], message: str) -> int:
        if not self._is_configured() or not phones:
            return 0
        numbers_str = ",".join(phones[:100])
        success = await self.send_sms(numbers_str, message)
        return len(phones) if success else 0

    def build_price_alert_message(
        self, crop: str, market: str, price: float,
        change_pct: float, language: str = "en"
    ) -> str:
        change_str = f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%"
        if language == "kn":
            return (
                f"ಕಿಸಾನ್ ಮಿತ್ರ: {crop} ಬೆಲೆ {market} ನಲ್ಲಿ "
                f"Rs.{price:.0f}/qtl ({change_str}). App ತೆರೆಯಿರಿ. -KISAAN"
            )
        return (
            f"Kisaan Mitra: {crop} at {market} is "
            f"Rs.{price:.0f}/qtl ({change_str}). Check app. -KISAAN"
        )

    def build_critical_alert_message(
        self, crop: str, market: str, price: float, language: str = "en"
    ) -> str:
        if language == "kn":
            return (
                f"URGENT: {crop} Rs.{price:.0f}/qtl {market}ನಲ್ಲಿ "
                f"- 7 ದಿನದ ಗರಿಷ್ಠ! ಈಗ ಮಾರಾಟ ಮಾಡಿ. -KISAAN"
            )
        return (
            f"URGENT Kisaan Mitra: {crop} at Rs.{price:.0f}/qtl "
            f"in {market} - 7-DAY HIGH! Sell NOW. -KISAAN"
        )

    def build_inactive_reminder_message(
        self, name: str, language: str = "en"
    ) -> str:
        if language == "kn":
            return (
                f"ನಮಸ್ಕಾರ {name}! ಕಿಸಾನ್ ಮಿತ್ರ App ತೆರೆಯಿರಿ - "
                f"ಹೊಸ ಮಂಡಿ ಬೆಲೆಗಳು ಕಾಯುತ್ತಿವೆ. -KISAAN"
            )
        return (
            f"Hello {name}! Open Kisaan Mitra - "
            f"New mandi prices are waiting. -KISAAN"
        )


sms_service = SMSService()