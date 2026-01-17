import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Purpose:
# - Read staged legacy data (stg_clients)
# - Deduplicate
# - Load clean data into core table (customers)
# - Idempotent (safe to re-run)

pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
pg_cur = pg_conn.cursor()

pg_cur.execute("""
INSERT INTO customers (
    name,
    legal_name,
    document,
    email,
    phone,
    type,
    active
)
SELECT DISTINCT ON (
    COALESCE(document, name || '-' || legacy_empresa_id)
)
    -- Operational name (fantasy)
    name,

    -- Legal registered name
    legal_name,

    -- CPF / CNPJ (may be null)
    document,

    email,
    phone,

    -- Domain decision: coming from CD_Cliente
    'customer' AS type,

    -- Legacy status mapping
    CASE
        WHEN status_raw = 'A' THEN true
        ELSE false
    END AS active

FROM stg_clients

-- Pick the most recent record per logical customer
ORDER BY
    COALESCE(document, name || '-' || legacy_empresa_id),
    imported_at DESC

ON CONFLICT (document)
DO NOTHING;
""")

pg_conn.commit()

print("Customers loaded from staging.")
