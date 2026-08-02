import re
import datetime
import uuid
from . import db
from .crypto import CryptoManager


class Api:
    def __init__(self):
        db.init_db()
        self.crypto = CryptoManager()
        self._eml_rgx = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    def _valid_eml(self, eml):
        return bool(self._eml_rgx.match(eml))

    def generate_license(self, eml: str, hw: str, months: float = 6):
        try:
            eml: str = eml.strip().lower()
            months: float = float(months)

            if not self._valid_eml(eml):
                return {"ok": False, "error": "Invalid email"}

            if months > 12:
                return {"ok": False, "error": "Max 12 months"}

            days: float = months * 30.0

            if db.check_hardware_exists(hw):
                return {"ok": False, "error": "Hardware already registered"}

            lic = {
                "user": eml,
                "issued": str(datetime.date.today()),
                "expires": str(datetime.date.today() + datetime.timedelta(days=days)),
                "license_id": str(uuid.uuid4()),
                "hardware_id": hw,
            }

            signature = self.crypto.sign_license(lic)

            lic_data = {
                "license": lic,
                "signature": signature,
            }

            db.save_license(eml, hw, lic["expires"], lic["license_id"])

            return {"ok": True, "license": lic_data}

        except Exception as e:
            return {"ok": False, "error": str(e)}
