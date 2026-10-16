"""
Modelo de Persistencia para Estudios de Densitometría Ósea (DXA)
Gestiona el almacenamiento relacional de mediciones, T/Z-scores y comparativas evolutivas.
"""

import json
from typing import Optional, Dict, Any, List
from carpeta_app.models.database_sql import get_db_connection


class EstudioDxaModel:
    @staticmethod
    def create(
        paciente_id: int,
        peso_kg: Optional[float],
        talla_cm: Optional[float],
        imc: Optional[float],
        categoria_imc: str,
        grupo_diagnostico: str,
        es_posmenopausica: bool,
        tiene_fractura_fragilidad: bool,
        datos_mediciones: Dict[str, Any],
        diagnostico_global: str,
        score_minimo: Optional[float],
        tipo_score_aplicado: str,
        sitio_critico: str,
        comparativa_evolutiva: Optional[Dict[str, Any]],
        informe_texto: str,
        medico_responsable: str
    ) -> int:
        """
        Inserta un nuevo registro de estudio DXA en SQLite.
        :return: ID primario del estudio creado.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO estudios_dxa (
                    paciente_id, peso_kg, talla_cm, imc, categoria_imc,
                    grupo_diagnostico, es_posmenopausica, tiene_fractura_fragilidad,
                    datos_mediciones_json, diagnostico_global, score_minimo,
                    tipo_score_aplicado, sitio_critico, comparativa_evolutiva_json,
                    informe_texto, medico_responsable
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paciente_id,
                    peso_kg,
                    talla_cm,
                    imc,
                    categoria_imc,
                    grupo_diagnostico,
                    1 if es_posmenopausica else 0,
                    1 if tiene_fractura_fragilidad else 0,
                    json.dumps(datos_mediciones, ensure_ascii=False),
                    diagnostico_global,
                    score_minimo,
                    tipo_score_aplicado,
                    sitio_critico,
                    json.dumps(comparativa_evolutiva, ensure_ascii=False) if comparativa_evolutiva else None,
                    informe_texto,
                    medico_responsable
                )
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_by_id(estudio_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera un estudio DXA por su ID junto con la demografía del paciente.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, p.cedula_id, p.nombre AS paciente_nombre, p.edad AS paciente_edad,
                       p.sexo AS paciente_sexo, p.medico_solicitante
                FROM estudios_dxa e
                JOIN pacientes p ON e.paciente_id = p.id
                WHERE e.id = ?
                """,
                (estudio_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["datos_mediciones"] = json.loads(res["datos_mediciones_json"]) if res.get("datos_mediciones_json") else {}
            res["comparativa_evolutiva"] = json.loads(res["comparativa_evolutiva_json"]) if res.get("comparativa_evolutiva_json") else None
            return res
        finally:
            conn.close()

    @staticmethod
    def list_recent(limit: int = 15) -> List[Dict[str, Any]]:
        """
        Lista los estudios DXA más recientes para el dashboard.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.id, e.fecha_estudio, e.diagnostico_global, e.score_minimo, e.tipo_score_aplicado,
                       p.nombre AS paciente_nombre, p.cedula_id, p.edad, p.sexo
                FROM estudios_dxa e
                JOIN pacientes p ON e.paciente_id = p.id
                ORDER BY e.created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
