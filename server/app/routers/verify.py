import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import License
from ..schemas import VerifyRequest, VerifyResponse

router = APIRouter(prefix="/api/v1/licenses", tags=["verify"])


@router.post("/verify", response_model=VerifyResponse)
def verify_license(
    payload: VerifyRequest, db: Session = Depends(get_db)
) -> VerifyResponse:
    lic = db.query(License).filter(License.license_id == payload.license_id).first()

    if lic is None:
        # Servidor não conhece essa licença (ex.: emitida antes da migração).
        # Cliente trata isso como "sem opinião" e cai no fallback local.
        return VerifyResponse(valid=False, reason="not_found")

    if lic.hardware_id != payload.hardware_id:
        return VerifyResponse(valid=False, reason="hardware_mismatch")

    if lic.status == "revoked":
        return VerifyResponse(valid=False, reason="revoked")

    if lic.expires_at < datetime.datetime.utcnow():
        return VerifyResponse(valid=False, reason="expired")

    return VerifyResponse(
        valid=True, status=lic.status, expires=lic.expires_at.date().isoformat()
    )
