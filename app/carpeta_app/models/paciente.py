"""
Modelo de Persistencia para la Entidad Paciente
Gestiona el registro unificado y búsqueda de pacientes en SQLite con consultas parametrizadas.
"""

from typing import Optional, Dict, Any, List
from carpeta_app.models.database_sql import get_db_connection


class PacienteModel:
    @staticmethod
    def get_or_create(
        cedula_id: str,
        nombre: str,
        edad: int,
        sexo: str,
        telefono: str = "",
        medico_solicitante: str = ""
    ) -> int:
        """
        Busca un paciente existente por cédula/ID o lo inserta si es nuevo.
        Actualiza los datos demográficos si ya existía.
        :return: ID primario del paciente en SQLite.
        """
        cedula_clean = cedula_id.strip()
        nombre_clean = nombre.strip()
        sexo_clean = sexo.strip().upper()
        if sexo_clean not in ('M', 'F'):
            sexo_clean = 'F'

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pacientes WHERE cedula_id = ?", (cedula_clean,))
            row = cursor.fetchone()
            if row:
                paciente_id = row["id"]
                cursor.execute(
                    """
                    UPDATE pacientes
                    SET nombre = ?, edad = ?, sexo = ?, telefono = ?, medico_solicitante = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (nombre_clean, edad, sexo_clean, telefono.strip(), medico_solicitante.strip(), paciente_id)
                )
                conn.commit()
                return paciente_id
            else:
                cursor.execute(
                    """
                    INSERT INTO pacientes (cedula_id, nombre, edad, sexo, telefono, medico_solicitante)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (cedula_clean, nombre_clean, edad, sexo_clean, telefono.strip(), medico_solicitante.strip())
                )
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def find_by_id(paciente_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un paciente por su ID primario.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Búsqueda autocompletable de pacientes por cédula o nombre.
        """
        term = f"%{query.strip()}%"
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, cedula_id, nombre, edad, sexo, medico_solicitante
                FROM pacientes
                WHERE cedula_id LIKE ? OR nombre LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (term, term, limit)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
