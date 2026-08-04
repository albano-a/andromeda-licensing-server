"""Create the PostgreSQL database used by the server.

Usage:
    python server/scripts/create_database.py

Environment variables:
    DATABASE_URL
        Full application connection string. The database part is used as the
        target database name.
    POSTGRES_MAINTENANCE_DB
        Optional maintenance database to connect to before creating the target
        database. Defaults to ``postgres``.
    POSTGRES_ADMIN_URL
        Optional full URL to a privileged Postgres connection. If set, it takes
        precedence over ``DATABASE_URL`` for connection details.

The script is idempotent: if the target database already exists, it exits
without making changes.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def _read_database_name_from_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.path or parsed.path == "/":
        raise ValueError("DATABASE_URL must include a database name")
    return parsed.path.lstrip("/")


def _build_connection_url(database_url: str, maintenance_db: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("DATABASE_URL must be a valid PostgreSQL URL")

    scheme = parsed.scheme
    if "+" in scheme:
        scheme = scheme.split("+", 1)[0]
    if scheme == "postgres":
        scheme = "postgresql"

    path = "/" + maintenance_db.lstrip("/")
    return urlunparse(
        (
            scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def main() -> None:
    admin_url = os.getenv("POSTGRES_ADMIN_URL")
    app_database_url = os.getenv("DATABASE_URL")

    if not app_database_url:
        raise SystemExit("DATABASE_URL is required")

    target_database = _read_database_name_from_url(app_database_url)

    if admin_url:
        connection_url = _build_connection_url(
            admin_url, os.getenv("POSTGRES_MAINTENANCE_DB", "postgres")
        )
    else:
        connection_url = _build_connection_url(
            app_database_url, os.getenv("POSTGRES_MAINTENANCE_DB", "postgres")
        )

    with psycopg2.connect(connection_url) as conn:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (target_database,),
            )
            exists = cur.fetchone() is not None

            if exists:
                print(f"Database '{target_database}' already exists")
                return

            cur.execute(sql.SQL("CREATE DATABASE {} ").format(sql.Identifier(target_database)))
            print(f"Database '{target_database}' created successfully")


if __name__ == "__main__":
    main()
