"""
Notification history routes.
Lets farmers see all past alerts sent to them.
"""

from fastapi import APIRouter, Depends, Query, Header, HTTPException
from typing import List
from bson import ObjectId

from app.models.schemas import NotificationResponse
from app.utils.database import get_db
from app.api.auth import get_current_user
from app.config import settings

router = APIRouter()


async def _get_user_from_header(
    authorization: str = Header(...),
    db=Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    return await get_current_user(token, db)


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(20, le=100),
    skip: int = Query(0, ge=0),
    user=Depends(_get_user_from_header),
    db=Depends(get_db),
):
    """
    Get notification history for the logged-in farmer.
    Sorted by most recent first.
    """
    user_id = str(user["_id"])

    cursor = db.notifications.find(
        {"user_id": user_id}
    ).sort("created_at", -1).skip(skip).limit(limit)

    records = await cursor.to_list(length=limit)

    return [
        NotificationResponse(
            id=str(r["_id"]),
            alert_type=r["alert_type"],
            commodity=r.get("commodity", ""),
            market=r.get("market", ""),
            old_price=r.get("old_price", 0),
            new_price=r.get("new_price", 0),
            change_pct=r.get("change_pct", 0),
            message_en=r.get("message_en", ""),
            firebase_sent=r.get("firebase_sent", False),
            sms_sent=r.get("sms_sent", False),
            status=r.get("status", "sent"),
            created_at=r["created_at"],
        )
        for r in records
    ]


@router.get("/notifications/unread-count")
async def get_unread_count(
    user=Depends(_get_user_from_header),
    db=Depends(get_db),
):
    """Return count of unread notifications for badge display."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=1)
    count = await db.notifications.count_documents({
        "user_id": str(user["_id"]),
        "created_at": {"$gte": since},
    })
    return {"unread_count": count}
