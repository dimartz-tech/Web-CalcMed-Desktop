"""
Motor de Cálculo de Biomarcadores Séricos Hepáticos
Implementa los algoritmos FIB-4, APRI y De Ritis (AST/ALT) para correlación bimodal con elastografía.
"""

import math
from typing import Dict, Any, Optional


def calculate_fib4(age: int, ast: float, alt: float, platelets: float) -> Optional[Dict[str, Any]]:
    """
    Calcula el índice de fibrosis FIB-4:
    FIB-4 = (Edad * AST) / (Plaquetas * sqrt(ALT))
    :param age: Edad en años.
    :param ast: Aspartato aminotransferasa (U/L).
    :param alt: Alanina aminotransferasa (U/L).
    :param platelets: Plaquetas en 10^3/uL o 10^9/L (ej. 250).
    :return: Diccionario con score y estratificación de riesgo.
    """
    if age <= 0 or ast <= 0 or alt <= 0 or platelets <= 0:
        return None

    score = (age * ast) / (platelets * math.sqrt(alt))
    score = round(score, 2)

    # Umbral ajustado por edad (≥ 65 años el umbral bajo sube a 2.0)
    low_cutoff = 2.0 if age >= 65 else 1.30
    high_cutoff = 2.67

    if score < low_cutoff:
        risk_label = "Bajo Riesgo de Fibrosis Avanzada (F0-F1)"
        badge_class = "badge-success"
        recommendation = "Valor predictivo negativo > 90%. Descarte confiable de fibrosis avanzada en la mayoría de etiologías."
    elif score <= high_cutoff:
        risk_label = "Riesgo Indeterminado / Zona Gris (F2)"
        badge_class = "badge-warning"
        recommendation = "Resultado no concluyente. Se recomienda evaluación con elastografía hepática o pruebas complementarias."
    else:
        risk_label = "Alto Riesgo de Fibrosis Avanzada / Cirrosis (F3-F4)"
        badge_class = "badge-danger"
        recommendation = "Alta probabilidad de fibrosis severa. Requiere valoración prioritaria por hepatología."

    return {
        "score": score,
        "risk_label": risk_label,
        "badge_class": badge_class,
        "recommendation": recommendation,
        "low_cutoff": low_cutoff,
        "high_cutoff": high_cutoff
    }


def calculate_apri(ast: float, ast_uln: float, platelets: float) -> Optional[Dict[str, Any]]:
    """
    Calcula el índice APRI (AST to Platelet Ratio Index):
    APRI = ((AST / LSN_AST) * 100) / Plaquetas
    :param ast: AST medida (U/L).
    :param ast_uln: Límite Superior Normal de AST del laboratorio (ej. 40 U/L).
    :param platelets: Plaquetas en 10^3/uL (ej. 250).
    :return: Diccionario con score APRI y estratificación.
    """
    if ast <= 0 or ast_uln <= 0 or platelets <= 0:
        return None

    score = ((ast / ast_uln) * 100.0) / platelets
    score = round(score, 2)

    if score < 0.50:
        risk_label = "Bajo Riesgo de Fibrosis Significativa"
        badge_class = "badge-success"
    elif score <= 1.00:
        risk_label = "Riesgo Indeterminado / Fibrosis Moderada"
        badge_class = "badge-warning"
    else:
        risk_label = "Alto Riesgo de Fibrosis Significativa / Cirrosis"
        badge_class = "badge-danger"

    return {
        "score": score,
        "risk_label": risk_label,
        "badge_class": badge_class
    }


def calculate_deritis(ast: float, alt: float) -> Optional[Dict[str, Any]]:
    """
    Calcula el ratio de De Ritis (AST / ALT).
    - < 1.0: Típico de MASLD/MASH, hepatitis viral no cirrótica.
    - >= 1.0: Sugestivo de progresión a fibrosis o cirrosis.
    - >= 2.0: Típico de hepatopatía alcohólica.
    """
    if ast <= 0 or alt <= 0:
        return None

    ratio = round(ast / alt, 2)
    if ratio < 1.0:
        interpretation = "Ratio < 1.0 (Patrón habitual en esteatosis/MASLD o daño hepatocelular inicial)"
    elif ratio < 2.0:
        interpretation = "Ratio entre 1.0 y 2.0 (Puede sugerir progresión de daño tisular / fibrosis)"
    else:
        interpretation = "Ratio ≥ 2.0 (Típico de hepatopatía por alcohol o cirrosis establecida)"

    return {
        "ratio": ratio,
        "interpretation": interpretation
    }
