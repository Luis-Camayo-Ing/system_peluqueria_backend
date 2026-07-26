from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies.database import get_db


router = APIRouter()


@router.get("/salud")
def comprobar_salud() -> dict[str, str]:
    return {"estado": "correcto"}


@router.get("/salud/base-datos")
def comprobar_base_datos(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "estado": "correcto",
        "base_datos": "conectada",
    }