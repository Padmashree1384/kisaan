"""
Authentication routes: register, login, token refresh.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt as _bcrypt
from bson import ObjectId

from app.models.schemas import UserRegister, UserLogin, Token, UserResponse, UserInDB
from app.utils.database import get_db
from app.config import settings

router = APIRouter()


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(token: str, db=None):
    """Decode JWT and return user document. Used as a dependency."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if db is None:
        db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    return user


# ── POST /register ─────────────────────────────────────────────────────────────

@router.post("/register", response_model=Token, status_code=201)
async def register(user_data: UserRegister, db=Depends(get_db)):
    """
    Register a new farmer.
    Stores hashed password and returns a JWT token immediately.
    """
    # Check if phone already registered
    existing = await db.users.find_one({"phone": user_data.phone})
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered. Please login.",
        )

    # Build user document
    user_doc = {
        "name": user_data.name,
        "phone": user_data.phone,
        "hashed_password": hash_password(user_data.password),
        "location_state": user_data.location_state,
        "location_district": user_data.location_district,
        "language": user_data.language.value,
        "crops": [c.model_dump() for c in user_data.crops],
        "fcm_token": None,
        "is_active": True,
        "last_active": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token({"sub": str(result.inserted_id), "phone": user_data.phone})

    return Token(
        access_token=token,
        user=_format_user(user_doc),
    )


# ── POST /login ────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db=Depends(get_db)):
    """
    Login with phone + password.
    Returns JWT access token valid for 30 days.
    """
    user = await db.users.find_one({"phone": credentials.phone})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    # Update last_active timestamp
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_active": datetime.utcnow()}},
    )

    token = create_access_token({"sub": str(user["_id"]), "phone": user["phone"]})

    return Token(
        access_token=token,
        user=_format_user(user),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_user(user_doc: dict) -> UserResponse:
    return UserResponse(
        id=str(user_doc["_id"]),
        name=user_doc["name"],
        phone=user_doc["phone"],
        location_state=user_doc["location_state"],
        location_district=user_doc["location_district"],
        language=user_doc.get("language", "en"),
        crops=user_doc.get("crops", []),
        last_active=user_doc.get("last_active", datetime.utcnow()),
        created_at=user_doc.get("created_at", datetime.utcnow()),
    )