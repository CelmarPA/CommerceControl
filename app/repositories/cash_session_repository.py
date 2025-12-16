# app/repositories/cash_session_repository.py

from sqlalchemy.orm import Session
from typing import Optional

from app.models.cash_session import CashSession


class CashSessionRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_open_by_user(self, user_id: int) -> Optional[CashSession]:
        return (
            self.db.query(CashSession)
            .filter(CashSession.user_id == user_id, CashSession.status == "open")
            .first()
        )

    def get_open_by_register(self, register_id: int) -> Optional[CashSession]:
        return(
            self.db.query(CashSession)
            .filter(CashSession.register_id == register_id, CashSession.status == "open")
            .first()
        )

    def create(self, session: CashSession) -> CashSession:
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)

        return session

    def close(self, session: CashSession) -> CashSession:
        self.db.flush()
        self.db.refresh(session)

        return session