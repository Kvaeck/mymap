# src/mymap/services/license_manager.py
import json
import pathlib
import time
from typing import Optional
import hmac
import hashlib

LICENSE_FILENAME = "pepik_license.json"
EXPORTS_FILENAME = "exports.json"

class LicenseManager:
    """
    Local license manager with a local license file.
    Supports:
    - is_full(): returns True if local license declares full mode
    - set_full_license(key): saves full license locally
    - clear_license()
    - (stub) activate_online(key, server_url) -> calls server activate endpoint
    """

    def __init__(self, data_dir: Optional[pathlib.Path] = None):
        if data_dir is None:
            data_dir = pathlib.Path.home() / ".pepik"
        self.data_dir = pathlib.Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.license_path = self.data_dir / LICENSE_FILENAME
        self.exports_path = self.data_dir / EXPORTS_FILENAME
        self._license = self._load_license()

    def _load_license(self):
        if self.license_path.exists():
            try:
                with open(self.license_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def is_full(self) -> bool:
        return self._license.get("mode") == "full"

    def set_full_license(self, key: str, issued_at: Optional[str] = None, expires_at: Optional[str] = None):
        if issued_at is None:
            issued_at = time.strftime("%Y-%m-%d")
        self._license = {
            "mode": "full",
            "key": key,
            "issued_at": issued_at,
            "expires_at": expires_at,
        }
        with open(self.license_path, "w", encoding="utf-8") as f:
            json.dump(self._license, f)

    def clear_license(self):
        self._license = {}
        try:
            self.license_path.unlink()
        except FileNotFoundError:
            pass

    # --- export counters persistence helpers ---
    def _read_exports(self):
        if self.exports_path.exists():
            try:
                with open(self.exports_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _write_exports(self, data):
        with open(self.exports_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def get_export_count(self, doc_hash: str) -> int:
        data = self._read_exports()
        return int(data.get(doc_hash, 0))

    def increment_export_count(self, doc_hash: str):
        data = self._read_exports()
        data[doc_hash] = int(data.get(doc_hash, 0)) + 1
        self._write_exports(data)

    # --- online activation stub (to implement server calls) ---
    def activate_online(self, license_key: str, server_url: str):
        """
        Placeholder for server activation. Implement HTTP call:
          POST {server_url}/activate {"license_key": license_key}
        If success -> call set_full_license(...)
        """
        raise NotImplementedError("Online activation is not implemented on client. Wire an HTTP client here.")

    # Optional: simple local check if license key is properly structured (very naive).
    @staticmethod
    def is_valid_key_structure(key: str) -> bool:
        # Basic format check: segments separated by '-'
        return isinstance(key, str) and len(key.split("-")) >= 3
