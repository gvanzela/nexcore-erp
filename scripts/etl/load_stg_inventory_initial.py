import os
import json
import uuid
import pyodbc
import psycopg2
from decimal import Decimal
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# CONFIGURATION — CHANGE ONLY THIS BLOCK FOR NEXT STAGING
# =========================================================

SOURCE_SYSTEM = "cmsys"

# Logical entity name inside staging (generic, not legacy table name)
SOURCE_ENTITY = "inventory_initial"

# Legacy table to extract from
LEGACY_QUERY = """
    SELECT *
    FROM dbo.OP_Inventario_Processo_Produto
"""

# Function that defines the business key (source_pk) for staging
# IMPORTANT:
# - Must uniquely identify one logical record
# - Must be stable across reloads
def build_source_pk(row: dict) -> str:
    return str(row.get("Cd_Produto"))


# =========================================================
# Helper: make legacy values JSON-safe
# =========================================================
def json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def row_to_dict(cursor, row):
    """
    Convert a pyodbc row to a JSON-safe dict using cursor metadata.
    """
    cols = [c[0] for c in cursor.description]
    out = {}
    for i, col in enumerate(cols):
        out[col] = json_safe(row[i])
    return out


def main():
    # =========================================================
    # 1) CONNECT TO SQL SERVER (LEGACY)
    # =========================================================
    mssql_conn = pyodbc.connect(
        f"DRIVER={{{os.getenv('MSSQL_DRIVER')}}};"
        f"SERVER={os.getenv('MSSQL_HOST')},{os.getenv('MSSQL_PORT')};"
        f"DATABASE={os.getenv('MSSQL_DB')};"
        f"UID={os.getenv('MSSQL_USER')};"
        f"PWD={os.getenv('MSSQL_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )
    mssql_cur = mssql_conn.cursor()

    # =========================================================
    # 2) CONNECT TO POSTGRES (NEXCORE — STAGING)
    # =========================================================
    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    pg_cur = pg_conn.cursor()

    batch_id = str(uuid.uuid4())

    try:
        # =========================================================
        # 3) EXTRACT — LEGACY INVENTORY (RAW)
        # =========================================================
        # No transformations, no assumptions.
        # This step only mirrors legacy rows into staging.
        mssql_cur.execute(LEGACY_QUERY)
        legacy_rows = mssql_cur.fetchall()
        rows = [row_to_dict(mssql_cur, r) for r in legacy_rows]

        # =========================================================
        # 4) LOAD — INSERT / UPSERT INTO stg_records
        # =========================================================
        insert_sql = """
            INSERT INTO stg_records (
                source_system,
                source_entity,
                source_pk,
                raw_payload,
                status,
                loaded_at,
                promoted_at,
                error_reason
            )
            VALUES (%s, %s, %s, %s::jsonb, %s, NOW(), NULL, NULL)
            ON CONFLICT (source_system, source_entity, source_pk)
            DO UPDATE SET
                raw_payload = EXCLUDED.raw_payload,
                status = 'NEW',
                loaded_at = NOW(),
                promoted_at = NULL,
                error_reason = NULL
        """

        inserted = 0

        for row in rows:
            source_pk = build_source_pk(row)
            if not source_pk:
                # Broken legacy row — ignore silently
                continue

            pg_cur.execute(
                insert_sql,
                (
                    SOURCE_SYSTEM,
                    SOURCE_ENTITY,
                    source_pk,
                    json.dumps(row, ensure_ascii=False),
                    "NEW",
                ),
            )
            inserted += 1

        pg_conn.commit()
        print(
            f"[OK] Inventory initial staging loaded | "
            f"batch_id={batch_id} | rows={inserted}"
        )

    except Exception:
        pg_conn.rollback()
        raise

    finally:
        try:
            pg_cur.close()
            pg_conn.close()
        finally:
            mssql_cur.close()
            mssql_conn.close()


if __name__ == "__main__":
    main()
