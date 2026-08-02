import base64
import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .config import settings


class CryptoManager:
    def __init__(self):
        self._priv = None
        self._load_key()

    def _load_key(self):
        with open(settings.private_key_path, "rb") as f:
            self._priv = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

    def sign_license(self, lic_data: dict) -> str:
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
