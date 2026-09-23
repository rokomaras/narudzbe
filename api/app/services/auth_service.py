# =============================================================
# auth_service.py — logika prijave, registracije i tokena
# =============================================================
# Service NE zna za HTTP (Request/Response), samo baca AppError.
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import RegisterRequest


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """Isti error za nepostojeći username i krivu lozinku:
    napadač ne može saznati koja korisnička imena postoje (enumeracija)."""
    user = await user_repo.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise AppError("invalid_credentials", "Pogrešno korisničko ime ili lozinka", 401)
    if not user.is_active:
        raise AppError("invalid_credentials", "Korisnički račun je deaktiviran", 401)
    return user


def create_tokens(user: User) -> tuple[str, str]:
    return create_access_token(user.id, user.role), create_refresh_token(user.id)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    """Iz valjanog REFRESH tokena izdaj novi par (access + refresh)."""
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AppError("invalid_credentials", "Nevažeći refresh token", 401)
    if payload.get("type") != "refresh":
        raise AppError("invalid_credentials", "Token nije refresh tipa", 401)

    user = await user_repo.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise AppError("invalid_credentials", "Korisnik ne postoji ili je deaktiviran", 401)
    return create_tokens(user)


async def register_customer(db: AsyncSession, body: RegisterRequest) -> User:
    """Javna registracija: UVIJEK role=customer (admina ne može napraviti nitko izvana)."""
    if await user_repo.get_by_username(db, body.username):
        raise AppError("duplicate", "Korisničko ime je već zauzeto", 409)
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role="customer",
        full_name=body.full_name,
        email=body.email,
        is_active=True,
    )
    return await user_repo.add(db, user)
