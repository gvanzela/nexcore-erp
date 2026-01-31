# scripts/xml/promote_purchase_in.py

import os
from decimal import Decimal
from datetime import datetime, UTC
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SOURCE_ENTITY = "purchase_xml"


def promote_purchase_in(matched_items, source_id: str):
    """
    Create inventory IN movements from matched XML items.

    - matched_items: list with product_id, quantity
    - source_id: invoice identifier (e.g., NF-e key)
    """

    pg = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = pg.cursor()

    try:
        for item in matched_items:
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
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    item["product_id"],
                    "IN",
                    Decimal(item["quantity"]),
                    datetime.now(UTC),
                    SOURCE_ENTITY,
                    source_id,
                ),
            )

        pg.commit()
        print("[OK] Purchase IN movements created")

    except Exception:
        pg.rollback()
        raise

    finally:
        cur.close()
        pg.close()


if __name__ == "__main__":
    """
    Manual test runner.
    Plug here the matched output from match_items_by_ean.
    """

    from match_items_by_ean import match_items_by_ean
    from read_nfe_xml import read_nfe_xml

    xml_items = read_nfe_xml(r"C:\Users\gabri\Downloads\35260104771370000345550010006486301879500382.xml")
    matched, _ = match_items_by_ean(xml_items)

    promote_purchase_in(
        matched_items=matched,
        source_id="NFE-TEST-001"
    )