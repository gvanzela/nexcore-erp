import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Promote products from staging to core
cur.execute("""
INSERT INTO products (
    code,
    name,
    short_name,
    description,
    barcode,
    unit
)
SELECT
    code,
    name,
    short_name,
    COALESCE(raw_payload->>'Ds_Texto_Explicativo', name),
    barcode,
    unit_sale
FROM stg_products
WHERE processed_at IS NULL
ON CONFLICT (code) DO NOTHING;
""")

# Mark staging rows as processed
cur.execute("""
UPDATE stg_products
SET processed_at = now()
WHERE processed_at IS NULL;
""")

conn.commit()
print("Products promoted.")
