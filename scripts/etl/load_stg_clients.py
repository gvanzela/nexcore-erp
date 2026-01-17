import os
import pyodbc
import psycopg2
import json
import uuid
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

def json_safe(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


# ---------- SQL Server ----------
mssql_conn = pyodbc.connect(
    f"DRIVER={{{os.getenv('MSSQL_DRIVER')}}};"
    f"SERVER={os.getenv('MSSQL_HOST')},{os.getenv('MSSQL_PORT')};"
    f"DATABASE={os.getenv('MSSQL_DB')};"
    f"UID={os.getenv('MSSQL_USER')};"
    f"PWD={os.getenv('MSSQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
mssql_cur = mssql_conn.cursor()

# ---------- Postgres ----------
pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
pg_cur = pg_conn.cursor()

batch_id = str(uuid.uuid4())

mssql_cur.execute("""
SELECT
    Cd_Empresa,        -- 0
    Cd_Cliente,        -- 1 (quase sempre NULL)
    Cd_Pessoa,         -- 2
    Cd_CPF_CNPJ,       -- 3 (fallback)
    Ds_Fantasia,       -- 4
    Ds_Razao_Social,   -- 5
    Ds_Email,          -- 6
    Cd_DDD_Telefone,   -- 7
    Ds_Telefone,       -- 8
    Cd_Status          -- 9
FROM dbo.CD_Cliente
""")

cols = [c[0] for c in mssql_cur.description]

for row in mssql_cur.fetchall():
    raw = {k: json_safe(v) for k, v in zip(cols, row)}

    legacy_cliente_id = (
        str(row[1]).strip()
        if row[1]
        else str(row[3]).strip()  # CPF/CNPJ como fallback
    )

    pg_cur.execute("""
        INSERT INTO stg_clients (
            source_system,
            legacy_empresa_id,
            legacy_cliente_id,
            legacy_pessoa_id,
            document,
            name,
            legal_name,
            email,
            phone,
            status_raw,
            raw_payload,
            import_batch_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (source_system, legacy_empresa_id, legacy_cliente_id)
        DO NOTHING;
    """, (
        "cmsys",
        str(row[0]),                    # empresa
        legacy_cliente_id,              # chave REAL agora
        str(row[2]) if row[2] else None,
        row[3],                         # document
        row[4],                         # name (fantasia)
        row[5],                         # legal_name
        row[6],                         # email
        f"{row[7] or ''}{row[8] or ''}",
        str(row[9]),
        json.dumps(raw),
        batch_id
    ))

pg_conn.commit()

print("Carga concluída. Batch:", batch_id)
