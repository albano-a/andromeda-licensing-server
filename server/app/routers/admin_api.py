import datetime
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crypto import CryptoManager
from ..database import get_db
from ..models import AdminUser, License
from ..schemas import (
    AdminCreateRequest,
    LicenseCreateRequest,
    LicenseCreateResponse,
    LicenseOut,
)
from ..security import hash_password, require_login

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_login)])

_EMAIL_RGX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _get_crypto() -> CryptoManager:
    return CryptoManager()


@router.get("/licenses", response_model=list[LicenseOut])
def list_licenses(db: Session = Depends(get_db)):
    licenses = db.query(License).order_by(License.issued_at.desc()).all()
    return [LicenseOut.from_orm_license(lic) for lic in licenses]


@router.post("/licenses", response_model=LicenseCreateResponse)
def create_license(
    payload: LicenseCreateRequest,
    admin_id: str = Depends(require_login),
    db: Session = Depends(get_db),
):
    eml = payload.user_email.strip().lower()
    if not _EMAIL_RGX.match(eml):
        raise HTTPException(status_code=400, detail="Invalid email")

    if payload.months > 12:
        raise HTTPException(status_code=400, detail="Max 12 months")

    existing = (
        db.query(License)
        .filter(License.hardware_id == payload.hardware_id, License.status == "active")
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Hardware already registered")

    today = datetime.date.today()
    expires = today + datetime.timedelta(days=payload.months * 30.0)

    lic_payload = {
        "user": eml,
        "issued": str(today),
        "expires": str(expires),
        "license_id": str(uuid.uuid4()),
        "hardware_id": payload.hardware_id,
    }
    signature = _get_crypto().sign_license(lic_payload)
    license_json = {"license": lic_payload, "signature": signature}

    lic = License(
        license_id=lic_payload["license_id"],
        user_email=eml,
        hardware_id=payload.hardware_id,
        issued_at=datetime.datetime.combine(today, datetime.time.min),
        expires_at=datetime.datetime.combine(expires, datetime.time.min),
        status="active",
        signature=signature,
        license_json=license_json,
        created_by=admin_id,
    )
    db.add(lic)
    db.commit()
    db.refresh(lic)

    return LicenseCreateResponse(
        license=LicenseOut.from_orm_license(lic), license_json=license_json
    )


@router.post("/licenses/{license_row_id}/revoke", response_model=LicenseOut)
def revoke_license(license_row_id: str, db: Session = Depends(get_db)):
    lic = db.query(License).filter(License.id == license_row_id).first()
    if lic is None:
        raise HTTPException(status_code=404, detail="License not found")
    lic.status = "revoked"
    db.commit()
    db.refresh(lic)
    return LicenseOut.from_orm_license(lic)


@router.delete("/licenses/{license_row_id}")
def delete_license(license_row_id: str, db: Session = Depends(get_db)):
    lic = db.query(License).filter(License.id == license_row_id).first()
    if lic is None:
        raise HTTPException(status_code=404, detail="License not found")
    db.delete(lic)
    db.commit()
    return {"ok": True}


@router.get("/licenses/{license_row_id}/download")
def download_license(license_row_id: str, db: Session = Depends(get_db)):
    lic = db.query(License).filter(License.id == license_row_id).first()
    if lic is None or lic.license_json is None:
        raise HTTPException(status_code=404, detail="License JSON not available")
    return lic.license_json


@router.get("/admins", response_model=list[str])
def list_admins(db: Session = Depends(get_db)):
    return [a.username for a in db.query(AdminUser).order_by(AdminUser.created_at).all()]


@router.post("/admins")
def create_admin(payload: AdminCreateRequest, db: Session = Depends(get_db)):
    if db.query(AdminUser).filter(AdminUser.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    admin = AdminUser(username=payload.username, password_hash=hash_password(payload.password))
    db.add(admin)
    db.commit()
    return {"ok": True}
