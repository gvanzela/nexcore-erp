import os
import json
import uuid
import pyodbc
import psycopg2
from decimal import Decimal
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

SOURCE_SYSTEM = "cmsys"


# ---------------------------------------------------------
# Helper: make legacy values JSON-safe
# SQL Server often returns Decimal/Datetime, which JSON can't handle.
# ---------------------------------------------------------
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
    # 1) CONNECT TO SQL SERVER (LEGACY SYSTEM)
    # =========================================================
    # Why explicit connection:
    # - ETL must be standalone (no dependency on API internals)
    # - Sellable connector pattern
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
    # 2) CONNECT TO POSTGRES (NEXCORE ERP)
    # =========================================================
    # Destination database where universal staging lives.
    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    pg_cur = pg_conn.cursor()

    # Batch id allows tracking one ETL execution
    batch_id = str(uuid.uuid4())

    try:
        # =========================================================
        # 3) EXTRACT: ORDER HEADERS (raw)
        # =========================================================
        # Keep it raw: no domain decisions here.
        mssql_cur.execute("SELECT * FROM dbo.CD_Pedido_Venda")
        header_rows = mssql_cur.fetchall()
        headers = [row_to_dict(mssql_cur, r) for r in header_rows]

        # =========================================================
        # 4) EXTRACT: ORDER ITEMS (raw)
        # =========================================================
        mssql_cur.execute("SELECT * FROM dbo.CD_Pedido_Venda_Item")
        item_rows = mssql_cur.fetchall()
        items = [row_to_dict(mssql_cur, r) for r in item_rows]

        # =========================================================
        # 5) LOAD: INSERT/UPSERT INTO stg_records
        # =========================================================
        # We store two entities:
        # - order_header  (source_pk = Nr_Pedido)
        # - order_item    (source_pk = Nr_Pedido:Nr_Sequencia)
        #
        # Idempotency:
        # - enforced by UNIQUE (source_system, source_entity, source_pk)
        # - ON CONFLICT updates raw_payload + status reset to NEW
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

        # ---- Headers
        for row in headers:
            nr_pedido = row.get("Nr_Pedido")
            if nr_pedido is None:
                # If a legacy row is broken, skip it (promotion step will be stricter)
                continue

            pg_cur.execute(
                insert_sql,
                (
                    SOURCE_SYSTEM,
                    "order_header",
                    str(nr_pedido),
                    json.dumps(row, ensure_ascii=False),
                    "NEW",
                ),
            )

        # ---- Items
        for row in items:
            nr_pedido = row.get("Nr_Pedido")
            nr_seq = row.get("Nr_Sequencia")
            if nr_pedido is None or nr_seq is None:
                continue

            source_pk = f"{nr_pedido}:{nr_seq}"
            pg_cur.execute(
                insert_sql,
                (
                    SOURCE_SYSTEM,
                    "order_item",
                    source_pk,
                    json.dumps(row, ensure_ascii=False),
                    "NEW",
                ),
            )

        pg_conn.commit()
        print(f"[OK] Loaded staging records. batch_id={batch_id} headers={len(headers)} items={len(items)}")

    except Exception as exc:
        pg_conn.rollback()
        raise exc

    finally:
        try:
            pg_cur.close()
            pg_conn.close()
        finally:
            mssql_cur.close()
            mssql_conn.close()


if __name__ == "__main__":
    main()
