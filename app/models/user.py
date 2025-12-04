# app/models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import true
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    # role: 'admin' or 'user'
    role = Column(String, nullable=False, default='user', server_default='user')
    is_superuser = Column(Boolean, default=False, server_default='false')
    is_active = Column(Boolean, default=True, server_default='true', nullable=False)
    
    # Relationship
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"

# Add relationship to Tenant model
from app.models.tenant import Tenant
Tenant.users = relationship("User", back_populates="tenant")