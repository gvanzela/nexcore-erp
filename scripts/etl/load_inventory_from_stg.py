import os
import psycopg2
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime, UTC

load_dotenv()

SOURCE_SYSTEM = "cmsys"
SOURCE_ENTITY = "inventory_initial"


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
        # =====================================================
        # 1) FETCH NEW INVENTORY RECORDS FROM STAGING
        # =====================================================
        # Each staging row represents the FINAL stock balance
        # for one product at the moment of inventory closing.
        cur.execute(
            """
            SELECT id, source_pk, raw_payload
            FROM stg_records
            WHERE source_system = %s
              AND source_entity = %s
              AND status = 'NEW'
            """,
            (SOURCE_SYSTEM, SOURCE_ENTITY),
        )
        rows = cur.fetchall()

        for stg_id, source_pk, payload in rows:
            # -----------------------------------------------
            # 2) RESOLVE PRODUCT IN CORE
            # -----------------------------------------------
            # source_pk = legacy product code
            cur.execute(
                """
                SELECT id
                FROM products
                WHERE code = %s
                """,
                (source_pk,),
            )
            product_row = cur.fetchone()

            if not product_row:
                # Product must already exist in core
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='ERROR',
                        error_reason=%s
                    WHERE id=%s
                    """,
                    (f"Product not found for code {source_pk}", stg_id),
                )
                continue

            product_id = product_row[0]

            # -----------------------------------------------
            # 3) EXTRACT QUANTITY FROM LEGACY PAYLOAD
            # -----------------------------------------------
            # Qt_Produto represents the physical stock counted
            # during inventory processing.
            quantity = payload.get("Qt_Produto")

            if quantity is None:
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='ERROR',
                        error_reason=%s
                    WHERE id=%s
                    """,
                    ("Missing Qt_Produto in legacy payload", stg_id),
                )
                continue

            # -----------------------------------------------
            # 4) CREATE INVENTORY MOVEMENT (CORE)
            # -----------------------------------------------
            # This is an INITIAL stock adjustment.
            # Quantity is POSITIVE (IN).
            cur.execute(
                """
                INSERT INTO inventory_movements (
                    product_id,
                    movement_type,
                    quantity,
                    occurred_at,
                    source_entity,
                    source_id
                )
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    product_id,
                    "IN",
                    Decimal(quantity),
                    datetime.now(UTC),
                    SOURCE_ENTITY,
                    source_pk,
                ),
            )

            # -----------------------------------------------
            # 5) MARK STAGING ROW AS PROMOTED
            # -----------------------------------------------
            cur.execute(
                """
                UPDATE stg_records
                SET status='PROMOTED',
                    promoted_at=NOW()
                WHERE id=%s
                """,
                (stg_id,),
            )

        pg.commit()
        print("[OK] Inventory initial balance promoted successfully")

    except Exception as exc:
        pg.rollback()
        raise exc

    finally:
        cur.close()
        pg.close()


if __name__ == "__main__":
    main()
