import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class VerifyRequest(BaseModel):
    license_id: str
    hardware_id: str


class VerifyResponse(BaseModel):
    valid: bool
    status: Optional[str] = None
    expires: Optional[str] = None
    reason: Optional[
        Literal["revoked", "not_found", "expired", "hardware_mismatch"]
    ] = None


class LicenseCreateRequest(BaseModel):
    user_email: EmailStr
    hardware_id: str
    months: float = 6

    class Config:
        pass


class LicenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    license_id: str
    user_email: str
    hardware_id: str
    issued_at: datetime.datetime
    expires_at: datetime.datetime
    status: str
    notes: str
    has_signature: bool = False

    @classmethod
    def from_orm_license(cls, lic) -> "LicenseOut":
        data = {
            "id": lic.id,
            "license_id": lic.license_id,
            "user_email": lic.user_email,
            "hardware_id": lic.hardware_id,
            "issued_at": lic.issued_at,
            "expires_at": lic.expires_at,
            "status": lic.status,
            "notes": lic.notes or "",
            "has_signature": lic.signature is not None,
        }
        return cls(**data)


class LicenseCreateResponse(BaseModel):
    license: LicenseOut
    license_json: dict  # o {"license": {...}, "signature": "..."} pronto pra baixar


class AdminCreateRequest(BaseModel):
    username: str
    password: str
