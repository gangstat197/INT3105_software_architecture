from sqlalchemy import text
from sqlalchemy.orm import Session


def ping_database(db: Session) -> None:
    db.execute(text("SELECT 1")).scalar_one()
