"""
Price Routes — FIXED VERSION

WHAT CHANGED:
- Reads 'commodity' and 'market' fields (not commodity_slug/mandi_slug)
- /prices now works for users' selected crops
- /prices/trending aggregates from real prices stored by agmarket_service
- All field references match what agmarket_service.py stores
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Header
from typing import List, Optional
from datetime import datetime

from app.utils.database import get_db
from app.services.agmarket_service import agmarket_service
from app.models.schemas import PriceResponse
from app.api.auth import get_current_user

router = APIRouter()


async def _get_optional_user(
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """Optionally get user from token — prices are readable without auth too."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        return await get_current_user(token, db)
    except Exception:
        return None


@router.get("/prices", response_model=List[PriceResponse])
async def get_prices(
    commodity: Optional[str] = Query(None, description="Crop name e.g. Tomato"),
    state: Optional[str] = Query(None, description="State name e.g. Karnataka"),
    district: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db=Depends(get_db),
    current_user=Depends(_get_optional_user),
):
    """
    Get latest mandi prices.
    If logged in and no filters provided, returns prices for user's selected crops.
    """
    query = {}

    # If user is logged in and no specific commodity filter,
    # return prices for all their watched crops
    if current_user and not commodity:
        user_crops = current_user.get("crops", [])
        if user_crops:
            commodity_names = list({c["commodity"] for c in user_crops})
            state_names = list({c["state"] for c in user_crops})
            query["commodity"] = {"$in": commodity_names}
            if not state:
                query["state"] = {"$in": state_names}

    # Apply explicit filters (override above if provided)
    if commodity:
        query["commodity"] = {"$regex": commodity, "$options": "i"}
    if state:
        query["state"] = {"$regex": state, "$options": "i"}
    if district:
        query["district"] = {"$regex": district, "$options": "i"}
    if market:
        query["market"] = {"$regex": market, "$options": "i"}

    cursor = db.prices.find(query).sort("fetched_at", -1).limit(limit)
    records = await cursor.to_list(length=limit)

    if not records:
        return []

    results = []
    for r in records:
        # These fields MUST exist — they are stored by agmarket_service.py
        commodity_name = r.get("commodity", "")
        market_name = r.get("market", "")
        modal_price = r.get("modal_price", 0)

        if not commodity_name or not market_name or not modal_price:
            continue

        change_pct = await agmarket_service.calculate_change(
            commodity_name, market_name, modal_price
        )

        trend = None
        if change_pct is not None:
            if change_pct > 1:
                trend = "up"
            elif change_pct < -1:
                trend = "down"
            else:
                trend = "stable"

        results.append(PriceResponse(
            commodity=commodity_name,
            market=market_name,
            district=r.get("district", ""),
            state=r.get("state", ""),
            modal_price=modal_price,
            min_price=r.get("min_price", 0),
            max_price=r.get("max_price", 0),
            arrival_date=r.get("arrival_date", ""),
            change_pct=round(change_pct, 2) if change_pct is not None else None,
            trend=trend,
        ))

    return results


@router.get("/prices/history")
async def get_price_history(
    commodity: str = Query(...),
    market: str = Query(...),
    days: int = Query(7, le=30),
    db=Depends(get_db),
):
    """Get price history for chart display in the app."""
    records = await agmarket_service.get_price_history(commodity, market, days)

    history = []
    for r in records:
        history.append({
            "date": r.get("arrival_date") or r["fetched_at"].strftime("%d/%m/%Y"),
            "modal_price": r.get("modal_price", 0),
            "min_price": r.get("min_price", 0),
            "max_price": r.get("max_price", 0),
        })

    return {"commodity": commodity, "market": market, "history": history}


@router.get("/prices/trending")
async def get_trending_crops(
    state: Optional[str] = Query(None),
    limit: int = Query(5, le=20),
    db=Depends(get_db),
):
    """
    Get crops with biggest price movements.
    Shown on dashboard as 'Top Movers Today'.
    """
    # Build match stage
    match_stage = {}
    if state:
        match_stage["state"] = {"$regex": state, "$options": "i"}

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$sort": {"fetched_at": -1}},
        {
            "$group": {
                "_id": {
                    "commodity": "$commodity",
                    "market": "$market",
                },
                "latest": {"$first": "$$ROOT"},
            }
        },
        {"$limit": 50},
    ]

    records = await db.prices.aggregate(pipeline).to_list(length=50)

    trending = []
    for r in records:
        rec = r["latest"]
        commodity_name = rec.get("commodity", "")
        market_name = rec.get("market", "")
        modal_price = rec.get("modal_price", 0)

        if not commodity_name or not modal_price:
            continue

        change = await agmarket_service.calculate_change(commodity_name, market_name, modal_price)

        if change is not None and abs(change) > 0.5:  # Only show meaningful changes
            trending.append({
                "commodity": commodity_name,
                "market": market_name,
                "state": rec.get("state", ""),
                "modal_price": modal_price,
                "change_pct": round(change, 2),
            })

    trending.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return trending[:limit]


@router.post("/prices/refresh")
async def manual_refresh(
    commodity: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
):
    """
    Manually trigger a price fetch from AgMarket.
    Use this to test if your API key works.

    Example: POST /api/v1/prices/refresh?commodity=Tomato&state=Karnataka
    """
    if not commodity or not state:
        return {"error": "Please provide both commodity and state. Example: ?commodity=Tomato&state=Karnataka"}

    stored = await agmarket_service.fetch_and_store(state=state, commodity=commodity)
    return {
        "message": f"Fetched and stored {stored} real price records from AgMarket",
        "count": stored,
        "note": "Check server logs for details" if stored == 0 else "Success!"
    }