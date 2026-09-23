from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.errors import AppError
from app.core.jwt import decode_token
from app.models.user import User
from app.repositories import user_repo

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError("invalid_credentials", "Token nije poslan", 401)

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise AppError("token_expired", "Token je istekao ili nije valjan", 401)

    if payload.get("type") != "access":
        raise AppError("invalid_credentials", "Token nije access tipa", 401)

    user = await user_repo.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise AppError(
            "invalid_credentials", "Korisnik ne postoji ili je deaktiviran", 401
        )
    return user


def require_role(*allowed_roles: str):
    """Return a dependency that permits only the specified roles."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AppError("forbidden", "Nemate dozvolu za ovu akciju", 403)
        return current_user

    return checker
