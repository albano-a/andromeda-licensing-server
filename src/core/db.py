import sqlite3
import datetime

DB_PATH = "src/core/security/license_users.db"


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        create table if not exists licenses (
            user text,
            hardware text unique,
            issued_at text,
            expires text,
            license_id text,
            count integer
        )
        """
    )

    # Migrate old schemas where user was unique, which prevented multiple rows per email.
    cur.execute("PRAGMA table_info(licenses)")
    columns = [row[1] for row in cur.fetchall()]
    cur.execute("PRAGMA index_list(licenses)")
    indexes = cur.fetchall()
    has_user_unique = False
    for index in indexes:
        index_name = index[1]
        is_unique = index[2]
        if is_unique:
            cur.execute(f"PRAGMA index_info({index_name})")
            index_columns = [r[2] for r in cur.fetchall()]
            if index_columns == ["user"]:
                has_user_unique = True
                break

    if has_user_unique:
        cur.execute(
            """
            create table licenses_new (
                user text,
                hardware text unique,
                issued_at text,
                expires text,
                license_id text,
                count integer,
                status text default 'Active',
                notes text default ''
            )
            """
        )
        issued_expr = "issued_at" if "issued_at" in columns else "date('now')"
        status_expr = "status" if "status" in columns else "'Active'"
        notes_expr = "notes" if "notes" in columns else "''"
        cur.execute(
            f"""
            insert into licenses_new (user, hardware, issued_at, expires, license_id, count, status, notes)
            select user, hardware, {issued_expr}, expires, license_id, count, {status_expr}, {notes_expr}
            from licenses
            """
        )
        cur.execute("drop table licenses")
        cur.execute("alter table licenses_new rename to licenses")

    # Add status column if it doesn't exist
    try:
        cur.execute("ALTER TABLE licenses ADD COLUMN status TEXT DEFAULT 'Active'")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Add notes column if it doesn't exist
    try:
        cur.execute("ALTER TABLE licenses ADD COLUMN notes TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # column already exists
    # Add issued_at column if it doesn't exist
    try:
        cur.execute("ALTER TABLE licenses ADD COLUMN issued_at TEXT")
        cur.execute("UPDATE licenses SET issued_at = date('now') WHERE issued_at IS NULL")
    except sqlite3.OperationalError:
        pass  # column already exists
    con.commit()
    con.close()


def load_licenses():
    con = sqlite3.connect("src/core/security/license_users.db")
    cur = con.cursor()
    cur.execute(
        "select user, hardware, issued_at, expires, status from licenses order by issued_at desc"
    )
    rows = cur.fetchall()
    con.close()

    return rows


def check_hardware_exists(hw):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("select 1 from licenses where hardware = ?", (hw,))
    row = cur.fetchone()
    con.close()
    return row is not None


def save_license(eml, hw, expires, license_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        insert into licenses (user, hardware, issued_at, expires, license_id, count)
        values (?, ?, ?, ?, ?, ?)
        """,
        (eml, hw, str(datetime.date.today()), expires, license_id, 1),
    )
    con.commit()
    con.close()


def delete_license(user, hardware):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("delete from licenses where user = ? and hardware = ?", (user, hardware))
    con.commit()
    con.close()
