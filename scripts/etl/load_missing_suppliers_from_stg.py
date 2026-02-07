import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SOURCE_SYSTEM = "cmsys"
SOURCE_ENTITY = "suppliers"


def normalize_doc(value: str) -> str:
    # Keep only digits (CPF/CNPJ)
    return "".join(c for c in value if c.isdigit()) if value else ""


def build_phone(ddd, phone):
    # Simple concat, MVP
    if ddd and phone:
        return f"{ddd}{phone}"
    return phone or None


def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    try:
        # -----------------------------------------------------
        # 1) Load suppliers from staging
        # -----------------------------------------------------
        cur.execute(
            """
            SELECT raw_payload
            FROM stg_records
            WHERE source_system = %s
              AND source_entity = %s
            """,
            (SOURCE_SYSTEM, SOURCE_ENTITY),
        )

        rows = cur.fetchall()
        inserted = 0

        # -----------------------------------------------------
        # 2) Insert missing suppliers into customers
        # -----------------------------------------------------
        for (payload,) in rows:
            document = normalize_doc(payload.get("Cd_CPF_CNPJ"))
            if not document:
                continue

            # Check if already exists in customers
            cur.execute(
                "SELECT 1 FROM customers WHERE document = %s",
                (document,),
            )
            if cur.fetchone():
                continue  # idempotent

            name = payload.get("Ds_Fantasia") or payload.get("Ds_Razao_social")
            legal_name = payload.get("Ds_Razao_social")
            email = payload.get("Ds_Email")
            phone = build_phone(
                payload.get("Cd_DDD_Telefone"),
                payload.get("Ds_Telefone"),
            )

            cur.execute(
                """
                INSERT INTO customers (
                    name,
                    legal_name,
                    document,
                    email,
                    phone,
                    type,
                    active
                )
                VALUES (%s, %s, %s, %s, %s, %s, true)
                """,
                (
                    name,
                    legal_name,
                    document,
                    email,
                    phone,
                    "supplier",
                ),
            )
            inserted += 1

        conn.commit()
        print(f"[OK] Missing suppliers inserted | rows={inserted}")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
