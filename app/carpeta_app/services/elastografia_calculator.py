"""
Motor de Cálculo Clínico para Elastografía Hepática Cuantitativa (SWE)
Basado en el Consenso SRU 2020 (Society of Radiologists in Ultrasound) y Criterios Baveno VII.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


def calculate_median_and_iqr(samples: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calcula la mediana y el rango intercuartílico (IQR = Q3 - Q1) a partir de un arreglo de mediciones.
    :param samples: Lista de mediciones numéricas válidas.
    :return: Tupla (mediana, iqr, ratio_iqr_mediana_pct).
    """
    valid = [float(x) for x in samples if x is not None and not math.isnan(float(x)) and float(x) > 0]
    if not valid:
        return None, None, None

    sorted_vals = sorted(valid)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    median = round(percentile(0.50), 2)
    q1 = percentile(0.25)
    q3 = percentile(0.75)
    iqr = round(q3 - q1, 2)

    ratio_pct = round((iqr / median) * 100.0, 1) if median > 0 else 0.0
    return median, iqr, ratio_pct


def validate_technical_quality(ratio_iqr_mediana_pct: float, unit: str = "kPa") -> Dict[str, Any]:
    """
    Evalúa si la adquisición cumple con los criterios de confiabilidad técnica según SRU/WFUMB.
    - Para kPa: IQR/Mediana <= 30%
    - Para m/s: IQR/Mediana <= 15%
    """
    is_kpa = (unit.lower() == "kpa")
    max_threshold = 30.0 if is_kpa else 15.0
    is_satisfactory = (ratio_iqr_mediana_pct <= max_threshold)

    if is_satisfactory:
        return {
            "is_valid": True,
            "quality_label": "Satisfactoria / Alta Confiabilidad",
            "badge_class": "badge-success",
            "threshold_used": f"≤ {max_threshold}%",
            "notes": "Variabilidad de muestra dentro de los límites de rigor clínico."
        }
    else:
        return {
            "is_valid": False,
            "quality_label": "Medición No Confiable (Variabilidad Excesiva)",
            "badge_class": "badge-danger",
            "threshold_used": f"≤ {max_threshold}%",
            "notes": f"Ratio IQR/Mediana ({ratio_iqr_mediana_pct}%) supera el umbral máximo ({max_threshold}%). Se recomienda repetir el muestreo."
        }


def classify_rigidity_sru_2020(median_kpa: float) -> Dict[str, Any]:
    """
    Aplica la "Regla de Cuatro" del Consenso SRU 2020 para estratificación de rigidez hepática.
    - <= 5.0 kPa: Normal / Descarte de fibrosis significativa.
    - < 9.0 kPa: Descarte de cACLD (Enfermedad Hepática Crónica Avanzada Compensada).
    - 9.0 a 13.0 kPa: Zona Gris / Sugestivo de fibrosis avanzada o cACLD.
    - > 13.0 kPa: Altamente sugestivo de cACLD (F3-F4).
    - > 17.0 kPa: Alta probabilidad de Hipertensión Portal Clínicamente Significativa (HPCS).
    """
    if median_kpa <= 5.0:
        return {
            "category_code": "NORMAL",
            "stage_label": "Normal / Sin Fibrosis Significativa",
            "badge_class": "badge-success",
            "cacld_risk": "Bajo / Excluido",
            "hpcs_risk": "Nulo / No aplicable",
            "recommendation": "Control periódico según indicación clínica de base. Alta probabilidad de parénquima normal."
        }
    elif median_kpa < 9.0:
        return {
            "category_code": "RULE_OUT_CACLD",
            "stage_label": "Descarte de cACLD (< 9.0 kPa)",
            "badge_class": "badge-info",
            "cacld_risk": "Descartado confiablemente",
            "hpcs_risk": "Nulo / Muy bajo",
            "recommendation": "En ausencia de otros signos clínicos o de laboratorio, se descarta enfermedad hepática avanzada compensada."
        }
    elif median_kpa <= 13.0:
        return {
            "category_code": "GRAY_ZONE",
            "stage_label": "Zona Gris / Sugestivo de cACLD (9.0 - 13.0 kPa)",
            "badge_class": "badge-warning",
            "cacld_risk": "Intermedio / Sugestivo",
            "hpcs_risk": "Indeterminado",
            "recommendation": "Zona gris de rigidez. Se recomienda correlación obligatoria con biomarcadores séricos (FIB-4 / APRI), control elastográfico evolutivo o biopsia hepática."
        }
    elif median_kpa <= 17.0:
        return {
            "category_code": "CACLD_ESTABLISHED",
            "stage_label": "Altamente Sugestivo de cACLD (> 13.0 kPa)",
            "badge_class": "badge-danger",
            "cacld_risk": "Alto / cACLD Probable (F3-F4)",
            "hpcs_risk": "Bajo a Moderado",
            "recommendation": "Alta probabilidad de fibrosis avanzada severa o cirrosis compensada. Requiere evaluación hepatológica integral."
        }
    else:
        return {
            "category_code": "HPCS_RISK",
            "stage_label": "cACLD con Alta Probabilidad de Hipertensión Portal (> 17.0 kPa)",
            "badge_class": "badge-danger",
            "cacld_risk": "Muy Alto / Cirrosis Establecida",
            "hpcs_risk": "Alta Probabilidad (Criterios Baveno VII)",
            "recommendation": "Riesgo elevado de hipertensión portal clínicamente significativa (HPCS). Se sugiere cribado endoscópico para descartar várices esofágicas según Baveno VII."
        }


def evaluate_elastography(
    samples: List[float],
    unit: str = "kPa",
    has_confounders: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Evaluación integral de elastografía hepática con control de calidad y detección de factores de confusión.
    """
    median, iqr, ratio_pct = calculate_median_and_iqr(samples)
    if median is None:
        return {
            "has_data": False,
            "error": "No se introdujeron mediciones válidas."
        }

    # Conversión referencial a kPa si los datos vinieron en m/s (E = 3 * rho * v^2 aprox)
    median_kpa = median if unit.lower() == "kpa" else round(3 * (median ** 2), 2)
    quality = validate_technical_quality(ratio_pct, unit)
    rigidity = classify_rigidity_sru_2020(median_kpa)

    # Evaluación de factores de confusión
    confounder_alerts = []
    if has_confounders:
        if has_confounders.get("alt_gt_5x", False):
            confounder_alerts.append("Hepatitis aguda / ALT > 5x LSN: puede sobreestimar falsamente la rigidez hepática.")
        if has_confounders.get("heart_failure", False):
            confounder_alerts.append("Insuficiencia cardíaca congestiva / congestión pasiva: elevación artificial de la rigidez.")
        if has_confounders.get("biliary_obstruction", False):
            confounder_alerts.append("Colestasis / obstrucción biliar extrahepática aguda presente.")
        if has_confounders.get("fasting_inadequate", False):
            confounder_alerts.append("Ayuno < 4 horas: el flujo esplácnico postprandial eleva la rigidez.")

    return {
        "has_data": True,
        "sample_count": len([x for x in samples if x is not None and float(x) > 0]),
        "unit": unit,
        "median": median,
        "median_kpa": median_kpa,
        "iqr": iqr,
        "ratio_iqr_mediana_pct": ratio_pct,
        "quality": quality,
        "rigidity": rigidity,
        "confounder_alerts": confounder_alerts
    }
