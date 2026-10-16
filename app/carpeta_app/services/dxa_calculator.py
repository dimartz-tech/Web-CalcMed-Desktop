"""
Motor de Cálculo Clínico para Densitometría Ósea (DXA)
Implementa los estándares oficiales de la International Society for Clinical Densitometry (ISCD).
"""

from typing import Dict, Any, List, Optional, Tuple


DIAGNOSTIC_GROUPS = {
    "POSTMENOPAUSAL": "postmenopausal",  # Mujer Posmenopáusica
    "MAN_50_PLUS": "man_50_plus",        # Hombre >= 50 años
    "PREMENOPAUSAL": "premenopausal",    # Mujer Premenopáusica
    "MAN_UNDER_50": "man_under_50"      # Hombre < 50 años
}


def calculate_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Tuple[Optional[float], str]:
    """
    Calcula el Índice de Masa Corporal (IMC) y determina la categoría nutricional según OMS.
    :param weight_kg: Peso corporal en kilogramos.
    :param height_cm: Talla en centímetros.
    :return: Tupla (imc, categoria_texto).
    """
    if weight_kg is None or height_cm is None or height_cm <= 0 or weight_kg <= 0:
        return None, ""

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)

    if bmi < 18.5:
        category = "Bajo peso"
    elif bmi < 25.0:
        category = "Normopeso"
    elif bmi < 30.0:
        category = "Sobrepeso"
    elif bmi < 35.0:
        category = "Obesidad Grado I"
    elif bmi < 40.0:
        category = "Obesidad Grado II"
    else:
        category = "Obesidad Grado III (Mórbida)"

    return bmi, category


def auto_determine_group(sex: str, age: int, is_postmenopausal: bool = True) -> str:
    """
    Determina automáticamente el grupo diagnóstico en base al sexo, edad y estado menopáusico.
    :param sex: 'F' o 'M'.
    :param age: Edad en años.
    :param is_postmenopausal: Booleano aplicable a mujeres.
    :return: Código del grupo diagnóstico ('postmenopausal', 'man_50_plus', 'premenopausal', 'man_under_50').
    """
    sex_clean = sex.upper().strip()
    if sex_clean == 'F':
        return DIAGNOSTIC_GROUPS["POSTMENOPAUSAL"] if (is_postmenopausal or age >= 50) else DIAGNOSTIC_GROUPS["PREMENOPAUSAL"]
    else:
        return DIAGNOSTIC_GROUPS["MAN_50_PLUS"] if age >= 50 else DIAGNOSTIC_GROUPS["MAN_UNDER_50"]


def get_tscore_category(t_score: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Evalúa el nivel de diagnóstico individual de un T-Score (Posmenopáusicas / Hombres >= 50 años).
    Criterios OMS / ISCD:
    - Normal: >= -1.0
    - Osteopenia (Masa ósea baja): entre -2.5 y -1.0
    - Osteoporosis: <= -2.5
    """
    if t_score is None:
        return None

    if t_score >= -1.0:
        return {
            "code": "NORMAL",
            "label": "Normal",
            "badge_class": "badge-success",
            "description": "Densidad mineral ósea normal (T-Score ≥ -1.0)"
        }
    elif t_score > -2.5:
        return {
            "code": "OSTEOPENIA",
            "label": "Masa Ósea Baja (Osteopenia)",
            "badge_class": "badge-warning",
            "description": "Masa ósea baja / Osteopenia (-2.5 < T-Score < -1.0)"
        }
    else:
        return {
            "code": "OSTEOPOROSIS",
            "label": "Osteoporosis",
            "badge_class": "badge-danger",
            "description": "Osteoporosis (T-Score ≤ -2.5)"
        }


def get_zscore_category(z_score: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Evalúa el nivel de diagnóstico individual de un Z-Score (Premenopáusicas / Hombres < 50 años).
    Criterios ISCD:
    - Dentro del rango esperado para la edad: > -2.0
    - Por debajo del rango esperado para la edad: <= -2.0
    """
    if z_score is None:
        return None

    if z_score > -2.0:
        return {
            "code": "EXPECTED",
            "label": "Dentro del Rango Esperado para la Edad",
            "badge_class": "badge-success",
            "description": "Z-Score > -2.0 (Dentro de los límites esperados)"
        }
    else:
        return {
            "code": "BELOW_EXPECTED",
            "label": "Por Debajo del Rango Esperado para la Edad",
            "badge_class": "badge-danger",
            "description": "Z-Score ≤ -2.0 (Baja densidad mineral ósea para la edad)"
        }


def calculate_change(prev_dmo: Optional[float], curr_dmo: Optional[float], lsc_threshold_pct: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Calcula la variación de densidad mineral ósea entre estudios y evalúa el Mínimo Cambio Significativo (LSC).
    :param prev_dmo: DMO previa en g/cm2.
    :param curr_dmo: DMO actual en g/cm2.
    :param lsc_threshold_pct: Umbral LSC en porcentaje (por defecto 3.0%).
    :return: Diccionario con delta absoluto, delta porcentual e interpretación estadística.
    """
    if prev_dmo is None or curr_dmo is None or prev_dmo <= 0:
        return None

    delta_abs = round(curr_dmo - prev_dmo, 4)
    delta_pct = round(((curr_dmo - prev_dmo) / prev_dmo) * 100.0, 2)

    is_significant = abs(delta_pct) >= lsc_threshold_pct
    if not is_significant:
        interpretation = "Sin cambio estadísticamente significativo respecto al estudio previo (dentro del LSC institucional)."
    elif delta_pct > 0:
        interpretation = f"Incremento estadísticamente significativo de DMO (+{delta_pct}%, supera el LSC de {lsc_threshold_pct}%)."
    else:
        interpretation = f"Pérdida ósea estadísticamente significativa de DMO ({delta_pct}%, supera el LSC de {lsc_threshold_pct}%)."

    return {
        "delta_abs": delta_abs,
        "delta_pct": delta_pct,
        "is_significant": is_significant,
        "interpretation": interpretation
    }


def evaluate_iscd(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluación diagnóstica global ISCD considerando todas las regiones anatómicas evaluadas.
    Determina el T/Z-Score más bajo, el sitio crítico y aplica el criterio de fractura por fragilidad.
    """
    group = data.get("group", DIAGNOSTIC_GROUPS["POSTMENOPAUSAL"])
    has_fragility_fracture = bool(data.get("has_fragility_fracture", False))
    is_adult_group = group in (DIAGNOSTIC_GROUPS["POSTMENOPAUSAL"], DIAGNOSTIC_GROUPS["MAN_50_PLUS"])

    valid_sites: List[Dict[str, Any]] = []

    def add_site(name: str, dmo: Any, t_score: Any, z_score: Any, note: str = ""):
        try:
            d_val = float(dmo) if dmo is not None and str(dmo).strip() != "" else None
        except ValueError:
            d_val = None

        try:
            t_val = float(t_score) if t_score is not None and str(t_score).strip() != "" else None
        except ValueError:
            t_val = None

        try:
            z_val = float(z_score) if z_score is not None and str(z_score).strip() != "" else None
        except ValueError:
            z_val = None

        if d_val is not None or t_val is not None or z_val is not None:
            valid_sites.append({
                "name": name,
                "dmo": d_val,
                "t_score": t_val,
                "z_score": z_val,
                "t_category": get_tscore_category(t_val),
                "z_category": get_zscore_category(z_val),
                "note": note
            })

    # 1. Columna Lumbar
    lumbar = data.get("lumbar", {})
    if lumbar.get("evaluate", True):
        region = lumbar.get("region", "L1-L4")
        add_site(f"Columna Lumbar ({region})", lumbar.get("dmo"), lumbar.get("t_score"), lumbar.get("z_score"), lumbar.get("notes", ""))

    # 2. Fémur Izquierdo
    femur_left = data.get("femur_left", {})
    if femur_left.get("evaluate", True):
        if femur_left.get("neck_t_score") is not None or femur_left.get("neck_dmo") is not None:
            add_site("Fémur Izq. - Cuello Femoral", femur_left.get("neck_dmo"), femur_left.get("neck_t_score"), femur_left.get("neck_z_score"))
        if femur_left.get("total_t_score") is not None or femur_left.get("total_dmo") is not None:
            add_site("Fémur Izq. - Fémur Total", femur_left.get("total_dmo"), femur_left.get("total_t_score"), femur_left.get("total_z_score"))

    # 3. Fémur Derecho
    femur_right = data.get("femur_right", {})
    if femur_right.get("evaluate", False):
        if femur_right.get("neck_t_score") is not None or femur_right.get("neck_dmo") is not None:
            add_site("Fémur Der. - Cuello Femoral", femur_right.get("neck_dmo"), femur_right.get("neck_t_score"), femur_right.get("neck_z_score"))
        if femur_right.get("total_t_score") is not None or femur_right.get("total_dmo") is not None:
            add_site("Fémur Der. - Fémur Total", femur_right.get("total_dmo"), femur_right.get("total_t_score"), femur_right.get("total_z_score"))

    # 4. Radio 33%
    radius33 = data.get("radius33", {})
    if radius33.get("evaluate", False):
        add_site("Antebrazo - Radio 33% (1/3)", radius33.get("dmo"), radius33.get("t_score"), radius33.get("z_score"), radius33.get("side", "No dominante"))

    if not valid_sites:
        return {
            "has_data": False,
            "global_diagnosis": "Sin datos suficientes",
            "badge_class": "badge-neutral",
            "lowest_score": None,
            "score_type": "T-Score" if is_adult_group else "Z-Score",
            "worst_site": "N/A",
            "sites": []
        }

    if is_adult_group:
        # Clasificación por T-Score más bajo
        t_scores = [(s["t_score"], s["name"]) for s in valid_sites if s["t_score"] is not None]
        if not t_scores:
            lowest_t = None
            worst_site = "N/A"
            global_diag = "Valores incompletos"
            badge = "badge-neutral"
        else:
            lowest_t, worst_site = min(t_scores, key=lambda x: x[0])
            if lowest_t >= -1.0:
                global_diag = "Normal"
                badge = "badge-success"
            elif lowest_t > -2.5:
                global_diag = "Osteopenia (Masa Ósea Baja)"
                badge = "badge-warning"
            else:
                if has_fragility_fracture:
                    global_diag = "Osteoporosis Severa (Establecida)"
                    badge = "badge-danger"
                else:
                    global_diag = "Osteoporosis"
                    badge = "badge-danger"

        return {
            "has_data": True,
            "is_adult": True,
            "global_diagnosis": global_diag,
            "badge_class": badge,
            "lowest_score": lowest_t,
            "score_type": "T-Score",
            "worst_site": worst_site,
            "has_fragility_fracture": has_fragility_fracture,
            "sites": valid_sites
        }
    else:
        # Clasificación por Z-Score más bajo
        z_scores = [(s["z_score"], s["name"]) for s in valid_sites if s["z_score"] is not None]
        if not z_scores:
            lowest_z = None
            worst_site = "N/A"
            global_diag = "Valores incompletos"
            badge = "badge-neutral"
        else:
            lowest_z, worst_site = min(z_scores, key=lambda x: x[0])
            if lowest_z > -2.0:
                global_diag = "Densidad Mineral Ósea Dentro del Rango Esperado para la Edad"
                badge = "badge-success"
            else:
                global_diag = "Densidad Mineral Ósea Por Debajo del Rango Esperado para la Edad"
                badge = "badge-danger"

        return {
            "has_data": True,
            "is_adult": False,
            "global_diagnosis": global_diag,
            "badge_class": badge,
            "lowest_score": lowest_z,
            "score_type": "Z-Score",
            "worst_site": worst_site,
            "sites": valid_sites
        }
