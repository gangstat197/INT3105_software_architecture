"""Create missing tables for a local development database."""

from backend.app.db.session import engine
from backend.app.models import Base


def main():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
