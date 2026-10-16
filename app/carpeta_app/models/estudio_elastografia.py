"""
Modelo de Persistencia para Estudios de Elastografía Hepática (SWE)
Almacena 10 mediciones cuantitativas, IQR/Mediana, Baveno VII y scores FIB-4/APRI.
"""

import json
from typing import Optional, Dict, Any, List
from carpeta_app.models.database_sql import get_db_connection


class EstudioElastografiaModel:
    @staticmethod
    def create(
        paciente_id: int,
        indicacion: str,
        etiologia: str,
        ayuno_adecuado: bool,
        factores_confusion: Dict[str, Any],
        muestras: List[float],
        unidad_medicion: str,
        mediana_kpa: float,
        iqr_kpa: float,
        ratio_iqr_mediana: float,
        calidad_tecnica: str,
        clasificacion_sru: str,
        riesgo_cacld: str,
        riesgo_hpcs: str,
        tiene_laboratorio: bool,
        ast_got: Optional[float],
        alt_gpt: Optional[float],
        plaquetas: Optional[float],
        fib4_score: Optional[float],
        fib4_estratificacion: Optional[str],
        apri_score: Optional[float],
        apri_estratificacion: Optional[str],
        deritis_ratio: Optional[float],
        informe_texto: str,
        medico_responsable: str
    ) -> int:
        """
        Inserta un nuevo registro de estudio de Elastografía Hepática en SQLite.
        :return: ID primario del estudio creado.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO estudios_elastografia (
                    paciente_id, indicacion, etiologia, ayuno_adecuado,
                    factores_confusion_json, muestras_json, unidad_medicion,
                    mediana_kpa, iqr_kpa, ratio_iqr_mediana, calidad_tecnica,
                    clasificacion_sru, riesgo_cacld, riesgo_hpcs, tiene_laboratorio,
                    ast_got, alt_gpt, plaquetas, fib4_score, fib4_estratificacion,
                    apri_score, apri_estratificacion, deritis_ratio, informe_texto,
                    medico_responsable
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paciente_id,
                    indicacion.strip(),
                    etiologia.strip(),
                    1 if ayuno_adecuado else 0,
                    json.dumps(factores_confusion, ensure_ascii=False),
                    json.dumps(muestras),
                    unidad_medicion,
                    mediana_kpa,
                    iqr_kpa,
                    ratio_iqr_mediana,
                    calidad_tecnica,
                    clasificacion_sru,
                    riesgo_cacld,
                    riesgo_hpcs,
                    1 if tiene_laboratorio else 0,
                    ast_got,
                    alt_gpt,
                    plaquetas,
                    fib4_score,
                    fib4_estratificacion,
                    apri_score,
                    apri_estratificacion,
                    deritis_ratio,
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
        Recupera un estudio de elastografía por su ID junto con la demografía del paciente.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, p.cedula_id, p.nombre AS paciente_nombre, p.edad AS paciente_edad,
                       p.sexo AS paciente_sexo, p.medico_solicitante
                FROM estudios_elastografia e
                JOIN pacientes p ON e.paciente_id = p.id
                WHERE e.id = ?
                """,
                (estudio_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["muestras"] = json.loads(res["muestras_json"]) if res.get("muestras_json") else []
            res["factores_confusion"] = json.loads(res["factores_confusion_json"]) if res.get("factores_confusion_json") else {}
            return res
        finally:
            conn.close()

    @staticmethod
    def list_recent(limit: int = 15) -> List[Dict[str, Any]]:
        """
        Lista las elastografías más recientes para el dashboard.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.id, e.fecha_estudio, e.mediana_kpa, e.ratio_iqr_mediana, e.clasificacion_sru,
                       e.calidad_tecnica, e.fib4_score, p.nombre AS paciente_nombre, p.cedula_id, p.edad, p.sexo
                FROM estudios_elastografia e
                JOIN pacientes p ON e.paciente_id = p.id
                ORDER BY e.created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
