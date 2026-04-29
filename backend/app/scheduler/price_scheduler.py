"""
Price Scheduler — FIXED VERSION

WHAT CHANGED:
- Only fetches crops that users have actually selected (no hardcoded list)
- Passes correct field names to alert_engine.process_price_update()
- Added clear logging so you can see the scheduler working
- Removed the hardcoded MONITORED_CROPS_STATES list
  (why fetch Wheat/Punjab when no user has selected that?)

Schedule: Every 30 minutes (configurable in .env via PRICE_FETCH_INTERVAL_MINUTES)
"""

import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config import settings
from app.utils.database import get_db

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def fetch_and_process_prices():
    """
    Main scheduled job — runs every 30 minutes.

    Step 1: Get all unique crop+state combinations from active users
    Step 2: Fetch real prices from AgMarket API for those crops
    Step 3: Store prices in DB
    Step 4: Compare with previous prices and fire alerts if thresholds crossed
    """
    from app.services.agmarket_service import agmarket_service
    from app.services.alert_engine import alert_engine

    start_time = datetime.now()
    print(f"\n⏰ [{start_time.strftime('%H:%M:%S IST')}] Starting price fetch job...")

    # Step 1: Get what users are actually watching
    user_crops = await _get_user_crop_preferences()

    if not user_crops:
        print("⚠️  No active user crop preferences found — nothing to fetch")
        print("   Ask users to register and select crops in the app first.")
        return

    print(f"📋 Fetching prices for {len(user_crops)} unique crop+state combinations:")
    for crop in user_crops:
        print(f"   - {crop['commodity']} in {crop['state']}")

    total_stored = 0

    # Step 2 & 3: Fetch and store prices for each crop+state
    for crop_pref in user_crops:
        commodity = crop_pref.get("commodity")
        state = crop_pref.get("state")

        if not commodity or not state:
            continue

        try:
            # Fetch from real AgMarket API and store in DB
            stored = await agmarket_service.fetch_and_store(
                state=state,
                commodity=commodity,
            )
            total_stored += stored

            if stored == 0:
                print(f"  ⚠️  No new records for {commodity}/{state} — API may have no data yet")
                continue

            # Step 4: Get what was just stored and run alert logic
            latest_records = await agmarket_service.get_latest_prices(
                commodity=commodity,
                state=state,
            )

            # Process each unique market (avoid duplicate alerts for same market)
            processed_markets = set()

            for record in latest_records:
                market = record.get("market")
                if not market:
                    continue

                market_key = (commodity.lower(), market.lower())
                if market_key in processed_markets:
                    continue
                processed_markets.add(market_key)

                # Get the previous price to calculate change
                previous_price = await _get_previous_price(
                    commodity=record["commodity"],
                    market=record["market"],
                    current_fetched_at=record.get("fetched_at"),
                )

                # Fire alert logic — this will send notifications if thresholds are met
                await alert_engine.process_price_update(
                    commodity=record["commodity"],
                    market=record["market"],
                    state=record["state"],
                    district=record.get("district", ""),
                    current_price=record["modal_price"],
                    previous_price=previous_price,
                )

        except Exception as e:
            print(f"❌ Error processing {commodity}/{state}: {e}")
            import traceback
            traceback.print_exc()

    elapsed = (datetime.now() - start_time).seconds
    print(f"✅ Price fetch complete. Stored {total_stored} records in {elapsed}s")


async def _get_user_crop_preferences() -> List[Dict[str, Any]]:
    """
    Get all unique commodity+state pairs from active users' crop preferences.
    Only fetches what users are actually watching — no wasted API calls.
    """
    db = get_db()

    pipeline = [
        # Only active users
        {"$match": {"is_active": True}},
        # Unwind crops array so we can group individual crops
        {"$unwind": "$crops"},
        # Only crops where alerts are enabled
        {"$match": {"crops.alert_enabled": True}},
        # Get unique commodity+state pairs
        {
            "$group": {
                "_id": {
                    "commodity": {"$toLower": "$crops.commodity"},
                    "state": {"$toLower": "$crops.state"},
                },
                # Keep the original casing for the API call
                "commodity": {"$first": "$crops.commodity"},
                "state": {"$first": "$crops.state"},
            }
        },
    ]

    result = await db.users.aggregate(pipeline).to_list(length=100)

    crops = []
    for r in result:
        commodity = r.get("commodity")
        state = r.get("state")
        if commodity and state:
            crops.append({"commodity": commodity, "state": state})

    return crops


async def _get_previous_price(
    commodity: str,
    market: str,
    current_fetched_at: Optional[datetime],
) -> Optional[float]:
    """
    Get the modal price from BEFORE the current fetch cycle.
    This is used to calculate % change.
    """
    db = get_db()

    query = {
        "commodity": {"$regex": f"^{re.escape(commodity)}$", "$options": "i"},
        "market": {"$regex": f"^{re.escape(market)}$", "$options": "i"},
    }

    # Get record just before the current one
    if current_fetched_at:
        query["fetched_at"] = {"$lt": current_fetched_at}

    record = await db.prices.find_one(
        query,
        sort=[("fetched_at", -1)],
    )

    if record:
        return record.get("modal_price")
    return None


def start_scheduler():
    """Register jobs and start APScheduler."""
    scheduler.add_job(
        fetch_and_process_prices,
        trigger=IntervalTrigger(minutes=settings.PRICE_FETCH_INTERVAL_MINUTES),
        id="price_fetch",
        name="Fetch Mandi Prices from AgMarket",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    scheduler.start()
    print(
        f"🕐 Scheduler started — fetching real AgMarket prices every "
        f"{settings.PRICE_FETCH_INTERVAL_MINUTES} minutes"
    )


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 Scheduler stopped")