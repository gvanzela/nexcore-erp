# scripts/xml/match_items_by_ean.py
# %%
import os
from typing import List, Dict
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def match_items_by_ean(items: List[Dict]):
    """
    Try to match XML items with core products using EAN (barcode).

    Returns:
    - matched items (with product_id)
    - unmatched items (needs manual review)
    """

    pg = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = pg.cursor()

    matched = []
    unmatched = []

    try:
        for item in items:
            ean = item.get("ean")

            if not ean:
                item["needs_review"] = True
                unmatched.append(item)
                continue

            # -------------------------------------------------
            # Try to find product by barcode / EAN
            # -------------------------------------------------
            cur.execute(
                """
                SELECT id, name
                FROM products
                WHERE barcode = %s
                """,
                (ean,),
            )
            row = cur.fetchone()

            if row:
                product_id, product_name = row
                item["product_id"] = product_id
                item["product_name"] = product_name
                item["needs_review"] = False
                matched.append(item)
            else:
                item["needs_review"] = True
                unmatched.append(item)

        return matched, unmatched

    finally:
        cur.close()
        pg.close()


if __name__ == "__main__":
    """
    Manual test runner.
    Plug here the output of read_nfe_xml.
    """

    from read_nfe_xml import read_nfe_xml

    xml_items = read_nfe_xml(r"C:\Users\gabri\Downloads\35260104771370000345550010006486301879500382.xml")

    matched, unmatched = match_items_by_ean(xml_items)

    print("MATCHED ITEMS")
    for i in matched:
        print(i)

    print("\nNEEDS REVIEW")
    for i in unmatched:
        print(i)
