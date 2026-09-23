# =============================================================
# logging.py — Konfiguracija logiranja
# =============================================================
# Python ima ugrađen logging modul. Ovdje ga konfiguriramo
# JEDNOM pri startu aplikacije, umjesto da svaki modul radi
# svoju konfiguraciju.
#
# Razine logiranja (od najdetaljnije do najkritičnije):
#   DEBUG → INFO → WARNING → ERROR → CRITICAL
#
# U dev okruženju logiramo sve (DEBUG+).
# U produkciji logiramo od INFO naviše (manje buke).
# =============================================================

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """
    Postavlja globalnu konfiguraciju logiranja.

    Poziva se jednom u create_app() (main.py).
    Sav output ide na stdout (standardni ispis) jer:
      - Docker/Railway skupljaju stdout logove automatski
      - Nema potrebe za log datotekama u kontejneru
    """
    level = logging.DEBUG if settings.ENV == "dev" else logging.INFO

    logging.basicConfig(
        level=level,
        # Format: timestamp | razina | ime loggera | poruka
        # Primjer: 2026-02-23 10:15:30 | INFO     | app.main | Server started
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Uvicorn po defaultu logira svaki request (GET /health 200 OK...).
    # To je previše buke za development, stišavamo na WARNING.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
