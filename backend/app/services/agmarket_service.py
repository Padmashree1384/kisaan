"""
AgMarket (data.gov.in) integration.
Fetches live mandi prices from India's government Open Data API.

API Docs: https://data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.config import settings
from app.utils.database import get_db


class AgMarketService:
    """
    Wrapper around the Agmarknet data.gov.in API.
    Handles fetching, parsing, and storing price records.
    """

    BASE_URL = settings.AGMARKET_BASE_URL

    async def fetch_prices(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Fetch price records from AgMarket API.
        Filters by state/commodity/district if provided.
        """
        params = {
            "api-key": settings.AGMARKET_API_KEY,
            "format": "json",
            "limit": limit,
            "offset": 0,
        }

        # Add optional filters
        filters = []
        if state:
            filters.append(f"state:{state}")
        if commodity:
            filters.append(f"commodity:{commodity}")
        if district:
            filters.append(f"district:{district}")
        if filters:
            params["filters[field]"] = filters

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            records = data.get("records", [])
            print(f"📦 Fetched {len(records)} price records from AgMarket")
            return records

        except httpx.HTTPError as e:
            print(f"❌ AgMarket API error: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error fetching prices: {e}")
            return []

    def parse_record(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a raw AgMarket API record into our schema.
        Handles missing/malformed fields gracefully.
        """
        try:
            return {
                "state": raw.get("state", "").strip(),
                "district": raw.get("district", "").strip(),
                "market": raw.get("market", "").strip(),
                "commodity": raw.get("commodity", "").strip(),
                "variety": raw.get("variety", "").strip(),
                "arrival_date": raw.get("arrival_date", "").strip(),
                "min_price": float(raw.get("min_price", 0) or 0),
                "max_price": float(raw.get("max_price", 0) or 0),
                "modal_price": float(raw.get("modal_price", 0) or 0),
                "fetched_at": datetime.utcnow(),
            }
        except (ValueError, TypeError) as e:
            print(f"⚠️  Could not parse record: {raw} — {e}")
            return None

    async def fetch_and_store(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
    ) -> int:
        """
        Fetch prices from AgMarket and persist to MongoDB.
        Returns the count of new records stored.
        """
        db = get_db()
        raw_records = await self.fetch_prices(state=state, commodity=commodity)

        stored = 0
        for raw in raw_records:
            parsed = self.parse_record(raw)
            if not parsed or parsed["modal_price"] <= 0:
                continue

            # Use upsert to avoid duplicates — key on commodity+market+arrival_date
            filter_key = {
                "commodity": parsed["commodity"],
                "market": parsed["market"],
                "district": parsed["district"],
                "state": parsed["state"],
                "arrival_date": parsed["arrival_date"],
            }
            await db.prices.update_one(
                filter_key,
                {"$set": parsed},
                upsert=True,
            )
            stored += 1

        print(f"✅ Stored/updated {stored} price records")
        return stored

    async def get_latest_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve the most recent price records for a commodity from DB.
        """
        db = get_db()
        query: Dict[str, Any] = {"commodity": {"$regex": commodity, "$options": "i"}}
        if state:
            query["state"] = {"$regex": state, "$options": "i"}
        if district:
            query["district"] = {"$regex": district, "$options": "i"}
        if market:
            query["market"] = {"$regex": market, "$options": "i"}

        cursor = db.prices.find(query).sort("fetched_at", -1).limit(20)
        return await cursor.to_list(length=20)

    async def get_price_history(
        self,
        commodity: str,
        market: str,
        days: int = 7,
    ) -> List[Dict]:
        """
        Get price history for a commodity+market over the last N days.
        Used to determine if current price is the highest in 7 days (critical alert).
        """
        db = get_db()
        since = datetime.utcnow() - timedelta(days=days)
        cursor = db.prices.find({
            "commodity": {"$regex": commodity, "$options": "i"},
            "market": {"$regex": market, "$options": "i"},
            "fetched_at": {"$gte": since},
        }).sort("fetched_at", 1)
        return await cursor.to_list(length=200)

    async def calculate_change(
        self,
        commodity: str,
        market: str,
        current_price: float,
    ) -> Optional[float]:
        """
        Calculate percentage change vs the previous price record.
        Returns None if no previous record exists.
        """
        db = get_db()
        # Get the two most recent records for this commodity+market
        cursor = db.prices.find({
            "commodity": {"$regex": commodity, "$options": "i"},
            "market": {"$regex": market, "$options": "i"},
        }).sort("fetched_at", -1).limit(2)

        records = await cursor.to_list(length=2)
        if len(records) < 2:
            return None

        prev_price = records[1].get("modal_price", 0)
        if prev_price == 0:
            return None

        return ((current_price - prev_price) / prev_price) * 100


# Singleton instance
agmarket_service = AgMarketService()
