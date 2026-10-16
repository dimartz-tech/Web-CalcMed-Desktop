"""
Módulo de Gestión de Conexiones SQLite con Integridad Referencial Forzada
Asegura consultas 100% parametrizadas y permisos seguros para Web-CalcMed.
"""

import os
import sqlite3
from typing import Optional

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Carpeta de datos escribible: junto al ejecutable portable si WEBCALCMED_DATA_DIR está definida,
# o la carpeta del proyecto en modo desarrollo.
DATA_DIR = os.environ.get("WEBCALCMED_DATA_DIR") or PACKAGE_DIR

DB_PATH = os.path.join(DATA_DIR, "databases", "sql", "calcmed.db")
SCHEMA_PATH = os.path.join(PACKAGE_DIR, "databases", "sql", "schema.sql")


def get_db_connection() -> sqlite3.Connection:
    """
    Establece y configura una conexión SQLite con soporte para nombres de columna tipo dict
    y activación forzada de claves foráneas.
    :return: Objeto sqlite3.Connection listo para usar.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Salvaguarda de integridad y concurrencia segura
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")

    # Restricción de permisos en archivo (0600)
    try:
        if os.path.exists(DB_PATH):
            os.chmod(DB_PATH, 0o600)
    except Exception:
        pass

    return conn


def init_db() -> None:
    """
    Inicializa las tablas e índices de la base de datos a partir del esquema DDL.
    """
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Esquema SQL no encontrado en {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
