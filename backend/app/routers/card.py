import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..schemas.deck import *

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/cards", 
    tags=["Cards"]
)