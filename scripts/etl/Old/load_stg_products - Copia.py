import os
import pyodbc
import psycopg2
import json
import uuid
from decimal import Decimal
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Helper: make legacy values JSON-safe
# SQL Server often returns Decimal, which JSON can't handle
# ---------------------------------------------------------
def json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value



# =========================================================
# 1) CONNECT TO SQL SERVER (LEGACY SYSTEM)
# =========================================================
# We read data from the old ERP (cmsys)
# No transformation here, only extraction
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
# This is where staging data lives
pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
pg_cur = pg_conn.cursor()

# Batch id allows us to track each import execution
batch_id = str(uuid.uuid4())


# =========================================================
# 3) READ ALL PRODUCTS FROM LEGACY TABLE
# =========================================================
# We select EVERYTHING from legacy.
# Business fields are extracted manually.
mssql_cur.execute("""
SELECT *
FROM dbo.CD_Produto
""")

columns = [c[0] for c in mssql_cur.description]


# =========================================================
# 4) LOAD INTO STAGING TABLE (stg_products)
# =========================================================
for row in mssql_cur.fetchall():

    # Full legacy row → JSON
    raw_payload = {
        k: json_safe(v)
        for k, v in zip(columns, row)
    }

    # Manual extraction of useful fields
    legacy_empresa = raw_payload.get("Cd_Empresa")
    legacy_code = raw_payload.get("Cd_Produto")

    pg_cur.execute("""
        INSERT INTO stg_products (
            source_system,
            legacy_empresa_id,
            legacy_product_code,

            code,
            name,
            short_name,
            description,
            barcode,
            unit_sale,
            unit_purchase,
            purchase_multiple,

            raw_payload,
            import_batch_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (source_system, legacy_empresa_id, legacy_product_code)
        DO NOTHING;
    """, (
        "cmsys",
        str(legacy_empresa),
        str(legacy_code),

        # Curated fields (used now)
        str(legacy_code),
        raw_payload.get("Ds_Produto"),
        raw_payload.get("Ds_Produto_Reduzida"),
        raw_payload.get("Ds_Texto_Explicativo"),
        raw_payload.get("CD_EAN_Produto"),
        raw_payload.get("Cd_Unidade_Medida_Venda"),
        raw_payload.get("Cd_Unidade_Medida_Compra"),
        raw_payload.get("Qt_Multiplo_Compra"),

        # Full legacy snapshot
        json.dumps(raw_payload),

        batch_id
    ))

# Persist changes
pg_conn.commit()

print("Products staged successfully. Batch:", batch_id)
