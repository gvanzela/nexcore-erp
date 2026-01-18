import os
import psycopg2
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
import re

load_dotenv()

SOURCE_SYSTEM = "cmsys"


# ---------------------------------------------------------
# Helper: normalize CPF/CNPJ
# - Keep only digits
# - CPF => 11 digits
# - CNPJ => 14 digits
# ---------------------------------------------------------
def normalize_document(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) in (11, 14):
        return digits
    return None


# ---------------------------------------------------------
# Helper: map legacy order status to core status
# ---------------------------------------------------------
def map_status(cd_situacao):
    return {
        1: "OPEN",
        2: "CONFIRMED",
        3: "CANCELED",
        4: "CLOSED",
        6: "OPEN",
    }.get(int(cd_situacao or 1), "OPEN")


def main():
    # =========================================================
    # CONNECT TO POSTGRES (NEXCORE ERP)
    # =========================================================
    # Standalone ETL:
    # - No dependency on API / SQLAlchemy
    # - Uses DATABASE_URL from .env
    pg = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = pg.cursor()

    try:
        # =====================================================
        # 1) FETCH NEW ORDER HEADERS FROM STAGING
        # =====================================================
        cur.execute("""
            SELECT id, raw_payload
            FROM stg_records
            WHERE source_system = %s
              AND source_entity = 'order_header'
              AND status = 'NEW'
        """, (SOURCE_SYSTEM,))
        headers = cur.fetchall()

        for stg_header_id, h in headers:
            # -----------------------------------------------
            # Extract and normalize legacy identifiers
            # -----------------------------------------------
            nr_pedido = h.get("Nr_Pedido")
            raw_doc = h.get("Cd_CPF_CNPJ")
            document = normalize_document(raw_doc)

            if not nr_pedido or not document:
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='ERROR',
                        error_reason=%s
                    WHERE id=%s
                    """,
                    ("Missing order number or invalid document", stg_header_id),
                )
                continue

            # -----------------------------------------------
            # 2) FIND CUSTOMER IN CORE BY DOCUMENT
            # -----------------------------------------------
            cur.execute(
                "SELECT id FROM customers WHERE document = %s",
                (document,),
            )
            row = cur.fetchone()

            if not row:
                # Customer SHOULD exist (you imported all legacy customers),
                # but we fail safely if it doesn't.
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='ERROR',
                        error_reason=%s
                    WHERE id=%s
                    """,
                    (f"Customer not found for document {document}", stg_header_id),
                )
                continue

            customer_id = row[0]

            # -----------------------------------------------
            # 3) FETCH ITEMS FOR THIS ORDER
            # -----------------------------------------------
            cur.execute("""
                SELECT id, raw_payload
                FROM stg_records
                WHERE source_system = %s
                  AND source_entity = 'order_item'
                  AND status = 'NEW'
                  AND source_pk LIKE %s
            """, (SOURCE_SYSTEM, f"{nr_pedido}:%"))
            items = cur.fetchall()

            if not items:
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='ERROR',
                        error_reason=%s
                    WHERE id=%s
                    """,
                    ("Order without items", stg_header_id),
                )
                continue

            # -----------------------------------------------
            # 4) CREATE ORDER (CORE)
            # -----------------------------------------------
            cur.execute("""
                INSERT INTO orders (
                    external_id,
                    customer_id,
                    issued_at,
                    status,
                    total_amount,
                    discount_amount,
                    notes,
                    active
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE)
                RETURNING id
            """, (
                str(nr_pedido),
                customer_id,
                h.get("Dt_Emissao"),
                map_status(h.get("Cd_Situacao_Pedido")),
                Decimal(h.get("Vl_Total_Pagar") or h.get("Vl_Total_Pedido") or 0),
                Decimal(h.get("Pc_Desc_Concedido") or 0),
                h.get("Ds_Obs"),
            ))
            order_id = cur.fetchone()[0]

            # -----------------------------------------------
            # 5) CREATE ORDER ITEMS (CORE)
            # -----------------------------------------------
            for stg_item_id, it in items:
                cur.execute("""
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        quantity,
                        unit_price,
                        discount_amount,
                        total_price,
                        notes
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (
                    order_id,
                    it.get("Cd_Produto"),
                    Decimal(it.get("Qt_Pedida") or 0),
                    Decimal(it.get("Vl_Unitario_Venda") or 0),
                    Decimal(it.get("Pc_Desc_Concedido") or 0),
                    Decimal(it.get("Qt_Pedida") or 0) * Decimal(it.get("Vl_Unitario_Venda") or 0),
                    it.get("Ds_Observacao_Produto"),
                ))

                # Mark item as promoted
                cur.execute(
                    """
                    UPDATE stg_records
                    SET status='PROMOTED',
                        promoted_at=NOW()
                    WHERE id=%s
                    """,
                    (stg_item_id,),
                )

            # Mark header as promoted
            cur.execute(
                """
                UPDATE stg_records
                SET status='PROMOTED',
                    promoted_at=NOW()
                WHERE id=%s
                """,
                (stg_header_id,),
            )

        pg.commit()
        print("[OK] Orders promoted successfully")

    except Exception as exc:
        pg.rollback()
        raise exc

    finally:
        cur.close()
        pg.close()


if __name__ == "__main__":
    main()
