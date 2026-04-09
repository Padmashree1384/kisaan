"""
Background scheduler using APScheduler.
Periodically fetches mandi prices and triggers alert evaluation.

Schedule:
  - Every 30 minutes: fetch prices from AgMarket API
  - Every 60 minutes: check for inactive users
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config import settings
from app.utils.database import get_db

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


# ── Popular crops and states to monitor ───────────────────────────────────────

MONITORED_CROPS_STATES = [
    {"commodity": "Tomato", "state": "Karnataka"},
    {"commodity": "Onion", "state": "Karnataka"},
    {"commodity": "Potato", "state": "Karnataka"},
    {"commodity": "Rice", "state": "Karnataka"},
    {"commodity": "Maize", "state": "Karnataka"},
    {"commodity": "Groundnut", "state": "Karnataka"},
    {"commodity": "Soyabean", "state": "Karnataka"},
    {"commodity": "Tomato", "state": "Maharashtra"},
    {"commodity": "Onion", "state": "Maharashtra"},
    {"commodity": "Wheat", "state": "Punjab"},
    {"commodity": "Rice", "state": "Punjab"},
]


async def fetch_and_process_prices():
    """
    Main scheduled job:
    1. Fetch latest prices from AgMarket API
    2. Compare with previous prices
    3. Trigger alert engine for each updated commodity
    """
    # Import here to avoid circular imports at module load
    from app.services.agmarket_service import agmarket_service
    from app.services.alert_engine import alert_engine

    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Running price fetch job...")

    # First, collect all user crop preferences to know what to fetch
    user_crops = await _get_user_crop_preferences()

    # Build unique set of commodity+state pairs to fetch
    to_fetch = set()
    for crop in MONITORED_CROPS_STATES:
        to_fetch.add((crop["commodity"], crop["state"]))
    for crop in user_crops:
        to_fetch.add((crop["commodity"], crop["state"]))

    total_stored = 0
    for commodity, state in to_fetch:
        try:
            # Fetch and store prices from API
            stored = await agmarket_service.fetch_and_store(
                state=state, commodity=commodity
            )
            total_stored += stored

            if stored == 0:
                continue

            # Get the freshest records just stored
            latest = await agmarket_service.get_latest_prices(
                commodity=commodity, state=state
            )

            # Process each market for this commodity
            processed_markets = set()
            for record in latest:
                market_key = (record["commodity"], record["market"])
                if market_key in processed_markets:
                    continue
                processed_markets.add(market_key)

                # Get previous price from DB (2nd most recent)
                previous_price = await _get_previous_price(
                    commodity=record["commodity"],
                    market=record["market"],
                    current_fetched_at=record.get("fetched_at"),
                )

                # Run alert logic
                await alert_engine.process_price_update(
                    commodity=record["commodity"],
                    market=record["market"],
                    state=record["state"],
                    district=record["district"],
                    current_price=record["modal_price"],
                    previous_price=previous_price,
                )

        except Exception as e:
            print(f"❌ Error processing {commodity}/{state}: {e}")

    print(f"✅ Price fetch complete. Stored {total_stored} records.")


async def _get_user_crop_preferences() -> List[Dict[str, Any]]:
    """Collect all unique crop+state preferences from registered users."""
    db = get_db()
    pipeline = [
        {"$unwind": "$crops"},
        {"$group": {
            "_id": None,
            "crops": {"$addToSet": {
                "commodity": "$crops.commodity",
                "state": "$crops.state",
            }}
        }}
    ]
    result = await db.users.aggregate(pipeline).to_list(length=1)
    if result:
        return result[0].get("crops", [])
    return []


async def _get_previous_price(
    commodity: str,
    market: str,
    current_fetched_at: Optional[datetime],
) -> Optional[float]:
    """
    Get the modal price from the record before the current fetch cycle.
    """
    db = get_db()
    query = {
        "commodity": {"$regex": commodity, "$options": "i"},
        "market": {"$regex": market, "$options": "i"},
    }
    if current_fetched_at:
        query["fetched_at"] = {"$lt": current_fetched_at}

    record = await db.prices.find_one(
        query,
        sort=[("fetched_at", -1)],
    )
    return record["modal_price"] if record else None


def start_scheduler():
    """Register jobs and start the APScheduler."""
    # Price fetch job
    scheduler.add_job(
        fetch_and_process_prices,
        trigger=IntervalTrigger(minutes=settings.PRICE_FETCH_INTERVAL_MINUTES),
        id="price_fetch",
        name="Fetch Mandi Prices",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    scheduler.start()
    print(
        f"🕐 Scheduler started — fetching prices every "
        f"{settings.PRICE_FETCH_INTERVAL_MINUTES} minutes"
    )


def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 Scheduler stopped")
