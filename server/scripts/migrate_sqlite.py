"""Migrate legacy SQLite license rows into the PostgreSQL server database.

This imports the old desktop app records from `license_users.db` into the
`licenses` table in PostgreSQL so they show up in the admin panel.

Imported legacy rows are not re-signed. They are stored with:
    - signature = None
    - license_json = None

Environment variables:
    SOURCE_SQLITE_PATH
        Optional path to the old SQLite database.
        Defaults to `src/core/security/license_users.db`.

    DATABASE_URL
        The PostgreSQL connection string for the new server database.
        Required because the script reuses the app models and session.
"""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
import sys
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import License  # noqa: E402

DEFAULT_SOURCE = ROOT_DIR.parent / "src" / "core" / "security" / "license_users.db"


def _parse_datetime(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.utcnow()

    raw = value.strip()
    if not raw:
        return dt.datetime.utcnow()

    try:
        parsed = dt.datetime.fromisoformat(raw)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(dt.timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    try:
        return dt.datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return dt.datetime.utcnow()


def _normalize_status(status_value: str | None, expires_at: dt.datetime) -> str:
    if status_value:
        normalized = status_value.strip().lower()
        if normalized in {"active", "revoked", "expired"}:
            return normalized

    return "expired" if expires_at < dt.datetime.utcnow() else "active"


def _load_legacy_rows(source_path: Path):
    con = sqlite3.connect(source_path)
    cur = con.cursor()
    cur.execute(
        "SELECT user, hardware, issued_at, expires, license_id, status, notes FROM licenses"
    )
    rows = cur.fetchall()
    con.close()
    return rows


def main() -> None:
    source_path = Path(os.getenv("SOURCE_SQLITE_PATH", str(DEFAULT_SOURCE)))
    if not source_path.exists():
        raise SystemExit(f"Source SQLite database not found: {source_path}")

    rows = _load_legacy_rows(source_path)
    if not rows:
        print("No legacy rows found")
        return

    session = SessionLocal()
    imported = 0
    skipped = 0

    try:
        for user_email, hardware_id, issued_at, expires, license_id, status, notes in rows:
            if not hardware_id or not user_email:
                skipped += 1
                continue

            existing = (
                session.query(License)
                .filter(
                    (License.hardware_id == hardware_id)
                    | (License.license_id == (license_id or ""))
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            issued_dt = _parse_datetime(issued_at)
            expires_dt = _parse_datetime(expires)
            normalized_status = _normalize_status(status, expires_dt)

            legacy_license_id = license_id or str(uuid.uuid4())

            session.add(
                License(  # type: ignore[arg-type]
                    license_id=legacy_license_id,
                    user_email=user_email.strip().lower(),
                    hardware_id=hardware_id.strip(),
                    issued_at=issued_dt,
                    expires_at=expires_dt,
                    status=normalized_status,
                    notes=(notes or "").strip(),
                    signature=None,
                    license_json=None,
                    created_by=None,
                    created_at=issued_dt,
                )
            )
            imported += 1

        session.commit()
        print(f"Imported {imported} legacy rows, skipped {skipped}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
