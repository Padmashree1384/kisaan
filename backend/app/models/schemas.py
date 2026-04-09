"""
Pydantic models for MongoDB documents.
These serve as both API schemas and database document shapes.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from bson import ObjectId


# ── Helpers ────────────────────────────────────────────────────────────────────

class PyObjectId(str):
    """Custom type to serialize MongoDB ObjectId as string."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# ── Enums ──────────────────────────────────────────────────────────────────────

class AlertType(str, Enum):
    NORMAL = "normal"           # Routine Firebase push
    BIG_JUMP = "big_jump"       # Firebase + SMS
    INACTIVE = "inactive"       # SMS only
    CRITICAL = "critical"       # SMS high priority

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class Language(str, Enum):
    ENGLISH = "en"
    KANNADA = "kn"
    HINDI = "hi"


# ── User ───────────────────────────────────────────────────────────────────────

class CropPreference(BaseModel):
    commodity: str          # e.g. "Tomato"
    state: str              # e.g. "Karnataka"
    district: str           # e.g. "Bengaluru"
    market: str             # e.g. "Bengaluru"
    alert_enabled: bool = True


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    location_state: str
    location_district: str
    language: Language = Language.ENGLISH
    crops: List[CropPreference] = []


class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$")
    password: str = Field(..., min_length=4)


class UserRegister(UserCreate):
    password: str = Field(..., min_length=4, description="Plain text password (hashed before storage)")


class UserInDB(BaseModel):
    """Shape of user document stored in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    phone: str
    hashed_password: str
    location_state: str
    location_district: str
    language: Language = Language.ENGLISH
    crops: List[CropPreference] = []
    fcm_token: Optional[str] = None     # Firebase device token
    is_active: bool = True
    last_active: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserResponse(BaseModel):
    """Safe user response (no password)."""
    id: str
    name: str
    phone: str
    location_state: str
    location_district: str
    language: Language
    crops: List[CropPreference]
    last_active: datetime
    created_at: datetime


class UpdatePreferences(BaseModel):
    crops: Optional[List[CropPreference]] = None
    language: Optional[Language] = None
    fcm_token: Optional[str] = None
    location_state: Optional[str] = None
    location_district: Optional[str] = None


# ── Price ──────────────────────────────────────────────────────────────────────

class PriceRecord(BaseModel):
    """Shape of price document stored in MongoDB (from AgMarket API)."""
    id: Optional[str] = Field(default=None, alias="_id")
    state: str
    district: str
    market: str
    commodity: str
    variety: str = ""
    arrival_date: str               # e.g. "01/07/2025"
    min_price: float
    max_price: float
    modal_price: float              # Most common traded price — primary metric
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class PriceResponse(BaseModel):
    commodity: str
    market: str
    district: str
    state: str
    modal_price: float
    min_price: float
    max_price: float
    arrival_date: str
    change_pct: Optional[float] = None  # % change vs previous record
    trend: Optional[str] = None         # "up" | "down" | "stable"


# ── Notification ───────────────────────────────────────────────────────────────

class NotificationRecord(BaseModel):
    """Stored in MongoDB for notification history."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    alert_type: AlertType
    commodity: str
    market: str
    old_price: float
    new_price: float
    change_pct: float
    message_en: str                 # English message
    message_kn: str = ""            # Kannada message
    firebase_sent: bool = False
    sms_sent: bool = False
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class NotificationResponse(BaseModel):
    id: str
    alert_type: AlertType
    commodity: str
    market: str
    old_price: float
    new_price: float
    change_pct: float
    message_en: str
    firebase_sent: bool
    sms_sent: bool
    status: NotificationStatus
    created_at: datetime


# ── Auth Token ─────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[str] = None
    phone: Optional[str] = None
