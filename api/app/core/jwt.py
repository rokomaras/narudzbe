# =============================================================
# jwt.py — izdavanje i provjera JWT tokena
# =============================================================
# Access token: kratkotrajan (15 min), šalje se uz svaki request.
# Refresh token: dugotrajan (7 dana), služi samo za dobivanje novog para.
# Payload: sub (user id), role, type ("access"/"refresh"), iss, exp.

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Vraća payload ili baca JWTError (istekao, kriv potpis, loš format)."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )
