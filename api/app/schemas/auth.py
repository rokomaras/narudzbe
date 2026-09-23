# =============================================================
# auth.py — Pydantic sheme za autentikaciju
# =============================================================
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=72)  # bcrypt gleda max 72 bajta
    full_name: str = Field(min_length=2, max_length=100)
    # jednostavna provjera oblika (bez dodatne biblioteke email-validator)
    email: str = Field(max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Namjerno NEMA password_hash: response_model filtrira što izlazi van."""

    id: int
    username: str
    role: str
    full_name: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
