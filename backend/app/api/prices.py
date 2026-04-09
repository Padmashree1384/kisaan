"""
Price routes — fetch live mandi prices for the app dashboard.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime

from app.utils.database import get_db
from app.services.agmarket_service import agmarket_service
from app.models.schemas import PriceResponse

router = APIRouter()


@router.get("/prices", response_model=List[PriceResponse])
async def get_prices(
    commodity: Optional[str] = Query(None, description="Crop name e.g. Tomato"),
    state: Optional[str] = Query(None, description="State name e.g. Karnataka"),
    district: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db=Depends(get_db),
):
    """
    Get latest mandi prices for a commodity.
    Includes % change vs previous record and trend indicator.
    """
    query = {}
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

    results = []
    for r in records:
        # Calculate price change vs the previous record for same commodity+market
        change_pct = await agmarket_service.calculate_change(
            r["commodity"], r["market"], r["modal_price"]
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
            commodity=r["commodity"],
            market=r["market"],
            district=r["district"],
            state=r["state"],
            modal_price=r["modal_price"],
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
    """
    Get price history for a commodity at a specific market.
    Used to render trend charts in the app.
    """
    records = await agmarket_service.get_price_history(commodity, market, days)

    history = [
        {
            "date": r.get("arrival_date") or r["fetched_at"].strftime("%d/%m/%Y"),
            "modal_price": r["modal_price"],
            "min_price": r.get("min_price", 0),
            "max_price": r.get("max_price", 0),
        }
        for r in records
    ]
    return {"commodity": commodity, "market": market, "history": history}


@router.get("/prices/trending")
async def get_trending_crops(
    state: Optional[str] = Query(None),
    limit: int = Query(5, le=20),
    db=Depends(get_db),
):
    """
    Get crops with the biggest price movements today.
    Shown on the home dashboard "top movers" section.
    """
    pipeline = [
        {"$sort": {"fetched_at": -1}},
        {"$group": {
            "_id": {"commodity": "$commodity", "market": "$market"},
            "latest": {"$first": "$$ROOT"},
        }},
        {"$limit": 50},
    ]
    records = await db.prices.aggregate(pipeline).to_list(length=50)

    trending = []
    for r in records:
        rec = r["latest"]
        change = await agmarket_service.calculate_change(
            rec["commodity"], rec["market"], rec["modal_price"]
        )
        if change is not None:
            trending.append({
                "commodity": rec["commodity"],
                "market": rec["market"],
                "state": rec["state"],
                "modal_price": rec["modal_price"],
                "change_pct": round(change, 2),
            })

    # Sort by absolute change descending
    trending.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return trending[:limit]


@router.post("/prices/refresh")
async def manual_refresh(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
):
    """
    Manually trigger a price fetch from AgMarket.
    Useful for testing and immediate refresh.
    """
    stored = await agmarket_service.fetch_and_store(state=state, commodity=commodity)
    return {"message": f"Fetched and stored {stored} price records", "count": stored}
