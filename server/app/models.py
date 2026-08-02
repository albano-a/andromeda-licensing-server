import datetime
import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class License(Base):
    __tablename__ = "licenses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    license_id = Column(String, unique=True, nullable=False, index=True)
    user_email = Column(String, nullable=False, index=True)
    hardware_id = Column(String, nullable=False, index=True)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(
        String, nullable=False, default="active"
    )  # active | revoked | expired
    notes = Column(Text, default="")

    signature = Column(Text, nullable=True)  # null para licenças legadas importadas
    license_json = Column(
        JSON, nullable=True
    )  # payload assinado completo {license, signature}

    created_by = Column(String, ForeignKey("admins.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("AdminUser")
