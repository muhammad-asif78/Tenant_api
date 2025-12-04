from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<Tenant {self.name}>"