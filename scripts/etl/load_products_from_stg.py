import os
import psycopg2
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime, UTC

load_dotenv()

SOURCE_SYSTEM = "cmsys"
SOURCE_ENTITY = "products"


def main():
    # =========================================================
    # CONNECT TO POSTGRES (NEXCORE ERP)
    # =========================================================
    # Standalone promotion step:
    # - Reads universal staging
    # - Writes to core domain
    # - No dependency on API / ORM
    pg = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = pg.cursor()

    try:
        # 1) Fetch products from staging
        cur.execute("""
            SELECT id, source_pk, raw_payload
            FROM stg_records
            WHERE source_system = %s
            AND source_entity = %s
        """, (SOURCE_SYSTEM, SOURCE_ENTITY))

        rows = cur.fetchall()

        for stg_id, source_pk, payload in rows:

            # Extract manufacturer_code from legacy payload
            manufacturer_code = payload.get("Cd_Fabricante")
            if not manufacturer_code:
                continue

            # Resolve product in core using legacy business key
            cur.execute(
                "SELECT id FROM products WHERE code = %s",
                (source_pk,),
            )
            row = cur.fetchone()
            if not row:
                continue

            product_id = row[0]

            # Update barcode
            cur.execute(
                """
                UPDATE products
                SET manufacturer_code = %s
                WHERE id = %s
                """,
                (str(manufacturer_code), product_id),
            )

            # Mark staging row as promoted
            cur.execute(
                """
                UPDATE stg_records
                SET status = 'PROMOTED',
                    promoted_at = NOW()
                WHERE id = %s
                """,
                (stg_id,),
            )
        pg.commit()
        print("[OK] Products Manufacurer Code promoted successfully")

    except Exception as exc:
        pg.rollback()
        raise exc

    finally:
        cur.close()
        pg.close()


if __name__ == "__main__":
    main()
