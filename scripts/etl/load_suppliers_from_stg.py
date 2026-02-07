import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SOURCE_SYSTEM = "cmsys"
SOURCE_ENTITY = "suppliers"


def normalize_doc(value: str) -> str:
    """
    Normalize CPF/CNPJ to digits only.
    Keeps comparison stable between legacy and core.
    """
    return "".join(c for c in value if c.isdigit()) if value else ""


def main():
    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    pg_cur = pg_conn.cursor()

    try:
        # ---------------------------------------------------------
        # 1) Load all supplier documents from staging
        # ---------------------------------------------------------
        pg_cur.execute(
            """
            SELECT source_pk
            FROM stg_records
            WHERE source_system = %s
              AND source_entity = %s
            """,
            (SOURCE_SYSTEM, SOURCE_ENTITY),
        )

        supplier_docs = {
            normalize_doc(r[0]) for r in pg_cur.fetchall() if r[0]
        }

        # ---------------------------------------------------------
        # 2) Fetch all customers from core
        # ---------------------------------------------------------
        pg_cur.execute(
            """
            SELECT id, document, type
            FROM customers
            """
        )

        customers = pg_cur.fetchall()

        updated = 0

        # ---------------------------------------------------------
        # 3) Promote customers to supplier / both (idempotent)
        # ---------------------------------------------------------
        for customer_id, document, current_type in customers:
            doc = normalize_doc(document)

            if doc not in supplier_docs:
                continue

            # Decide new type
            if current_type == "customer":
                new_type = "supplier"
            else:
                new_type = current_type  # supplier or both already

            if new_type != current_type:
                pg_cur.execute(
                    """
                    UPDATE customers
                    SET type = %s
                    WHERE id = %s
                    """,
                    (new_type, customer_id),
                )
                updated += 1

        pg_conn.commit()
        print(f"[OK] Suppliers promoted | updated={updated}")

    except Exception:
        pg_conn.rollback()
        raise

    finally:
        pg_cur.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
