from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health():
    """Provjera da API radi (koristi je i platforma za deploy)."""
    return {"status": "ok"}
