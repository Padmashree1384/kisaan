"""
AgMarket (data.gov.in) — FINAL WORKING VERSION

CONFIRMED FROM API RESPONSE:
- Field names are lowercase: state, district, market, commodity,
  arrival_date, min_price, max_price, modal_price
- Filter format uses lowercase field IDs: filters[state]=Karnataka
  NOT filters[State] (Title Case was wrong)
- API is live with 5947 total records as of April 2026
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.config import settings
from app.utils.database import get_db


class AgMarketService:

    BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    async def fetch_prices(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Fetch real mandi prices from data.gov.in.

        CORRECT filter format (confirmed from API field definitions):
          filters[state]=Karnataka   ← lowercase field id
          filters[commodity]=Tomato  ← lowercase field id
        """
        if not settings.AGMARKET_API_KEY:
            print("❌ AGMARKET_API_KEY not set in .env")
            return []

        # List of tuples to avoid any encoding issues
        params = [
            ("api-key", settings.AGMARKET_API_KEY),
            ("format", "json"),
            ("limit", str(limit)),
            ("offset", "0"),
        ]

        # CORRECT: lowercase field ids as confirmed by the API schema
        if state:
            params.append(("filters[state]", state))
        if commodity:
            params.append(("filters[commodity]", commodity))
        if district:
            params.append(("filters[district]", district))

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                print(f"🌐 AgMarket status: {response.status_code}")
                response.raise_for_status()
                data = response.json()

            if data.get("status") == "error":
                print(f"❌ API error: {data.get('message', '')[:200]}")
                return []

            records = data.get("records", [])
            total = data.get("total", 0)
            print(f"📦 AgMarket: {len(records)} records (total available: {total})")

            if records:
                print(f"   Sample: {records[0].get('commodity')} @ "
                      f"{records[0].get('market')} = "
                      f"₹{records[0].get('modal_price')}")

            return records

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
            return []
        except httpx.TimeoutException:
            print("⏱️  AgMarket timeout — will retry next cycle")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []

    def parse_record(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse raw AgMarket record.
        All field names are already lowercase from the API.
        """
        try:
            commodity = (raw.get("commodity") or "").strip()
            market = (raw.get("market") or "").strip()
            state = (raw.get("state") or "").strip()
            district = (raw.get("district") or "").strip()
            arrival_date = (raw.get("arrival_date") or "").strip()

            if not commodity or not market or not state:
                return None

            modal_price = float(raw.get("modal_price") or 0)
            if modal_price <= 0:
                return None

            return {
                "commodity": commodity,
                "market": market,
                "state": state,
                "district": district,
                "modal_price": modal_price,
                "min_price": float(raw.get("min_price") or 0),
                "max_price": float(raw.get("max_price") or 0),
                "variety": (raw.get("variety") or "").strip(),
                "grade": (raw.get("grade") or "").strip(),
                "arrival_date": arrival_date,
                "source": "agmarket",
                "fetched_at": datetime.utcnow(),
            }
        except (ValueError, TypeError) as e:
            print(f"⚠️  Parse error: {e}")
            return None

    async def fetch_and_store(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
    ) -> int:
        """Fetch real prices from AgMarket and upsert into MongoDB."""
        db = get_db()
        raw_records = await self.fetch_prices(state=state, commodity=commodity)

        if not raw_records:
            return 0

        stored = 0
        for raw in raw_records:
            parsed = self.parse_record(raw)
            if not parsed:
                continue

            # Upsert key — same commodity+market+state+date = same record
            filter_key = {
                "commodity": parsed["commodity"],
                "market": parsed["market"],
                "state": parsed["state"],
                "arrival_date": parsed["arrival_date"],
            }
            await db.prices.update_one(
                filter_key, {"$set": parsed}, upsert=True
            )
            stored += 1

        if stored > 0:
            print(f"✅ Stored/updated {stored} real price records in MongoDB")
        return stored

    async def get_latest_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
    ) -> List[Dict]:
        db = get_db()
        query: Dict[str, Any] = {
            "commodity": {"$regex": commodity, "$options": "i"}
        }
        if state:
            query["state"] = {"$regex": state, "$options": "i"}
        if district:
            query["district"] = {"$regex": district, "$options": "i"}
        if market:
            query["market"] = {"$regex": market, "$options": "i"}
        cursor = db.prices.find(query).sort("fetched_at", -1).limit(20)
        return await cursor.to_list(length=20)

    async def get_price_history(
        self, commodity: str, market: str, days: int = 7
    ) -> List[Dict]:
        db = get_db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = db.prices.find({
            "commodity": {"$regex": commodity, "$options": "i"},
            "market": {"$regex": market, "$options": "i"},
            "fetched_at": {"$gte": since},
        }).sort("fetched_at", 1)
        return await cursor.to_list(length=200)

    async def calculate_change(
        self, commodity: str, market: str, current_price: float
    ) -> Optional[float]:
        db = get_db()
        cursor = db.prices.find({
            "commodity": {"$regex": commodity, "$options": "i"},
            "market": {"$regex": market, "$options": "i"},
        }).sort("fetched_at", -1).limit(2)
        records = await cursor.to_list(length=2)
        if len(records) < 2:
            return None
        prev = records[1].get("modal_price", 0)
        if not prev:
            return None
        return ((current_price - prev) / prev) * 100


agmarket_service = AgMarketService()