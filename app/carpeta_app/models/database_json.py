"""
Gestor de Persistencia Documental JSON para Ajustes Institucionales y Membretes
Implementa escritura atómica para evitar corrupción de datos en concurrencia.
"""

import os
import json
import tempfile
from typing import Any, Dict

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get("WEBCALCMED_DATA_DIR") or PACKAGE_DIR
CONFIG_DIR = os.path.join(DATA_DIR, "databases", "config")
DEFAULT_SETTINGS_PATH = os.path.join(CONFIG_DIR, "default_settings.json")


def load_settings() -> Dict[str, Any]:
    """
    Carga la configuración institucional del archivo JSON con fallback a valores por defecto.
    :return: Diccionario con los ajustes de la clínica, médico y preferencias.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_SETTINGS_PATH):
        default_data = {
            "institucion": {
                "nombre_centro": "Centro de Diagnóstico Médico Especializado",
                "departamento": "Departamento de Diagnóstico por Imágenes",
                "direccion": "Av. Principal Médica #100",
                "telefono": "(809) 555-0199",
                "logo_url": ""
            },
            "medico": {
                "nombre": "Dr. Radiólogo Responsable",
                "especialidad": "Especialista en Radiología y Diagnóstico por Imágenes",
                "subespecialidad": "Densitometría Ósea / Ecografía Cuantitativa",
                "matricula": "123456",
                "exequatur": "987-65"
            },
            "preferencias": {
                "tema_defecto": "dark",
                "modo_efimero": False,
                "ast_uln_defecto": 40.0,
                "umbral_lsc_defecto": 3.0
            }
        }
        save_settings(default_data)
        return default_data

    try:
        with open(DEFAULT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: Dict[str, Any]) -> bool:
    """
    Guarda los ajustes institucionales mediante escritura atómica (tempfile + replace).
    :param data: Diccionario de configuración a persistir.
    :return: True si se guardó exitosamente, False en caso de error.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile("w", dir=CONFIG_DIR, delete=False, encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name

        os.replace(temp_name, DEFAULT_SETTINGS_PATH)
        try:
            os.chmod(DEFAULT_SETTINGS_PATH, 0o600)
        except Exception:
            pass
        return True
    except Exception as e:
        if "temp_name" in locals() and os.path.exists(temp_name):
            os.remove(temp_name)
        return False
