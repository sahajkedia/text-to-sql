import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from config import POSTGRES_CONFIG


@contextmanager
def get_connection():
    conn = psycopg.connect(
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
        dbname=POSTGRES_CONFIG["database"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
    )
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql: str) -> tuple[list[dict], list[str]]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            columns = [desc.name for desc in cur.description] if cur.description else []
            rows = [dict(row) for row in cur.fetchall()]
            return rows, columns


def get_schema_ddl() -> list[str]:
    query = """
    SELECT 
        'CREATE TABLE ' || schemaname || '.' || tablename || ' (' ||
        string_agg(
            column_name || ' ' || data_type || 
            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
            ', '
        ) || ');' AS ddl
    FROM (
        SELECT 
            c.table_schema AS schemaname,
            c.table_name AS tablename,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.ordinal_position
        FROM information_schema.columns c
        JOIN information_schema.tables t 
            ON c.table_name = t.table_name 
            AND c.table_schema = t.table_schema
        WHERE t.table_type = 'BASE TABLE'
            AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY c.table_schema, c.table_name, c.ordinal_position
    ) sub
    GROUP BY schemaname, tablename;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]


def get_table_names() -> list[str]:
    query = """
    SELECT table_schema || '.' || table_name AS full_name
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]


def test_connection() -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False
