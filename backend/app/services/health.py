from sqlalchemy.orm import Session, configure_mappers

from ..models import Base
from ..repositories.health import ping_database
from ..schemas.health import DatabaseHealth, ModelHealth, ModelInfo


def check_database(db: Session) -> DatabaseHealth:
    ping_database(db)
    return DatabaseHealth()


def check_models() -> ModelHealth:
    configure_mappers()
    models = [
        ModelInfo(
            name=mapper.class_.__name__,
            table=mapper.local_table.name,
            relationships={
                name: relation.mapper.class_.__name__
                for name, relation in mapper.relationships.items()
            },
        )
        for mapper in sorted(Base.registry.mappers, key=lambda m: m.class_.__name__)
    ]
    return ModelHealth(model_count=len(models), models=models)
