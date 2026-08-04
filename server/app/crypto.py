import base64
import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .config import settings


class CryptoManager:
    def __init__(self):
        self._priv = None

    def _ensure_key_loaded(self):
        if self._priv is None:
            self._load_key()

    def _load_key(self):
        key_bytes = None

        if settings.private_key_b64:
            raw_value = settings.private_key_b64.strip()
            if raw_value.startswith("-----BEGIN"):
                key_bytes = raw_value.encode()
            else:
                try:
                    key_bytes = base64.b64decode(raw_value)
                except Exception as exc:
                    raise RuntimeError(
                        "PRIVATE_KEY_B64 must contain base64-encoded PEM or raw PEM text"
                    ) from exc
        elif settings.private_key_pem:
            key_bytes = settings.private_key_pem.encode()
        else:
            raise RuntimeError("Private key is required via PRIVATE_KEY_B64 or PRIVATE_KEY_PEM")

        self._priv = serialization.load_pem_private_key(
            key_bytes, password=None, backend=default_backend()
        )

    def sign_license(self, lic_data: dict) -> str:
        self._ensure_key_loaded()
        lic_bytes = json.dumps(lic_data, sort_keys=True).encode()
        sig = self._priv.sign(
            lic_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(sig).decode()
