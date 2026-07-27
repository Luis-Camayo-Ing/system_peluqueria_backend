import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.service.model import Service


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, service: Service) -> Service:
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def get_by_id(self, service_id: uuid.UUID) -> Service | None:
        statement = select(Service).where(
            Service.id == service_id
        )

        return self.db.scalar(statement)

    def get_by_name(
        self,
        company_id: uuid.UUID,
        name: str,
    ) -> Service | None:
        statement = select(Service).where(
            Service.company_id == company_id,
            Service.name == name,
        )

        return self.db.scalar(statement)

    def get_all(
        self,
        company_id: uuid.UUID,
    ) -> list[Service]:
        statement = (
            select(Service)
            .where(Service.company_id == company_id)
            .order_by(Service.name)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        service: Service,
    ) -> Service:
        self.db.commit()
        self.db.refresh(service)
        return service

    def delete(
        self,
        service: Service,
    ) -> None:
        self.db.delete(service)
        self.db.commit()