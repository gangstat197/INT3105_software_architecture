import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..schemas.health import DatabaseHealth, ModelHealth
from ..services.health import check_database, check_models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("/db", response_model=DatabaseHealth)
def database_health(db: Annotated[Session, Depends(get_db)]) -> DatabaseHealth:
    """Check database connectivity with SELECT 1; does not check schema readiness."""
    try:
        return check_database(db)
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/models", response_model=ModelHealth)
def model_health() -> ModelHealth:
    """Resolve ORM relationships and list registered models without querying the DB."""
    return check_models()
