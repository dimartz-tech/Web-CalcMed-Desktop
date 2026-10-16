"""
Motor de Cálculo Clínico para Nódulos Tiroideos (ACR TI-RADS 2017)
Basado en el sistema estandarizado del American College of Radiology.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


COMPOSITION_SCORES = {
    "cystic": {"label": "Quístico o casi completamente quístico", "points": 0},
    "spongiform": {"label": "Espongiforme", "points": 0},
    "mixed": {"label": "Mixto quístico y sólido", "points": 1},
    "solid": {"label": "Sólido o casi completamente sólido", "points": 2}
}

ECHOGENICITY_SCORES = {
    "anechoic": {"label": "Anecogénico", "points": 0},
    "hyperechoic_isoechoic": {"label": "Hiperecoico o Isoecoico", "points": 1},
    "hypoechoic": {"label": "Hipoecoico", "points": 2},
    "very_hypoechoic": {"label": "Muy hipoecoico", "points": 3}
}

SHAPE_SCORES = {
    "wider_than_tall": {"label": "Más ancho que alto (Wider-than-tall)", "points": 0},
    "taller_than_wide": {"label": "Más alto que ancho (Taller-than-wide)", "points": 3}
}

MARGIN_SCORES = {
    "smooth": {"label": "Lisos / Bien definidos", "points": 0},
    "ill_defined": {"label": "Mal definidos", "points": 0},
    "lobulated_irregular": {"label": "Lobulados o Irregulares", "points": 2},
    "extra_thyroidal": {"label": "Extensión Extratiroidea franca", "points": 3}
}

ECHOGENIC_FOCI_SCORES = {
    "none_or_comet_tail": {"label": "Ninguno o grandes colas de cometa", "points": 0},
    "macrocalcifications": {"label": "Macrocalcificaciones", "points": 1},
    "peripheral_rim": {"label": "Calcificaciones periféricas / en cáscara", "points": 2},
    "punctate": {"label": "Focos puntiformes / Microcalcificaciones", "points": 3}
}


def calculate_nodule_dimensions(
    d_longitudinal: Any,
    d_anteroposterior: Any,
    d_transverse: Any
) -> Dict[str, Any]:
    """
    Calcula diámetro mayor, volumen elipsoide y relación de aspecto en plano axial.
    """
    def parse_val(v):
        try:
            val = float(v)
            return val if val > 0 else None
        except (ValueError, TypeError):
            return None

    l = parse_val(d_longitudinal)
    ap = parse_val(d_anteroposterior)
    t = parse_val(d_transverse)

    max_mm = 0.0
    for dim in (l, ap, t):
        if dim is not None and dim > max_mm:
            max_mm = dim

    max_cm = round(max_mm / 10.0, 2) if max_mm > 0 else 0.0

    volume_ml = None
    if l is not None and ap is not None and t is not None:
        vol = 0.523 * (l * ap * t) / 1000.0
        volume_ml = round(vol, 2)

    suggested_taller = bool(ap is not None and t is not None and ap > t)

    summary = (
        f"{l} × {ap} × {t} mm (Vol: {volume_ml} mL)"
        if (l and ap and t)
        else (f"Diámetro mayor: {max_mm} mm" if max_mm > 0 else "No especificadas")
    )

    return {
        "has_dimensions": max_mm > 0,
        "max_diameter_mm": max_mm,
        "max_diameter_cm": max_cm,
        "volume_ml": volume_ml,
        "suggested_taller": suggested_taller,
        "summary": summary
    }


def evaluate_tirads(nodule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa las 5 categorías ACR TI-RADS y determina categoría, puntaje y conducta.
    """
    comp_key = nodule_data.get("composition", "solid")
    comp_info = COMPOSITION_SCORES.get(comp_key, COMPOSITION_SCORES["solid"])
    comp_pts = comp_info["points"]

    echo_key = nodule_data.get("echogenicity", "hypoechoic")
    echo_info = ECHOGENICITY_SCORES.get(echo_key, ECHOGENICITY_SCORES["hypoechoic"])
    echo_pts = echo_info["points"]
    if comp_key == "cystic":
        echo_pts = 0

    shape_key = nodule_data.get("shape", "wider_than_tall")
    shape_info = SHAPE_SCORES.get(shape_key, SHAPE_SCORES["wider_than_tall"])
    shape_pts = shape_info["points"]

    margin_key = nodule_data.get("margin", "smooth")
    margin_info = MARGIN_SCORES.get(margin_key, MARGIN_SCORES["smooth"])
    margin_pts = margin_info["points"]

    foci = nodule_data.get("echogenicFoci") or nodule_data.get("echogenic_foci") or {}
    foci_pts = 0
    active_foci = []

    if foci.get("punctate"):
        foci_pts += 3
        active_foci.append("Focos ecogénicos puntiformes / microcalcificaciones (+3)")
    if foci.get("peripheral_rim"):
        foci_pts += 2
        active_foci.append("Calcificaciones periféricas en anillo (+2)")
    if foci.get("macrocalcifications"):
        foci_pts += 1
        active_foci.append("Macrocalcificaciones (+1)")
    if foci.get("none_comet_tail") or not active_foci:
        if not active_foci:
            active_foci.append("Ninguno o cola de cometa grande (0)")

    total_points = comp_pts + echo_pts + shape_pts + margin_pts + foci_pts

    if total_points == 0:
        cat_code = "TR1"
        cat_label = "TR1: Benigno"
        risk = "< 2% (Malignidad prácticamente descartada)"
    elif total_points <= 2:
        cat_code = "TR2"
        cat_label = "TR2: No Sospechoso"
        risk = "< 2% (Muy bajo riesgo de malignidad)"
    elif total_points == 3:
        cat_code = "TR3"
        cat_label = "TR3: Levemente Sospechoso"
        risk = "~5% (Riesgo bajo de malignidad)"
    elif total_points <= 6:
        cat_code = "TR4"
        cat_label = "TR4: Moderadamente Sospechoso"
        risk = "5% - 20% (Riesgo moderado de malignidad)"
    else:
        cat_code = "TR5"
        cat_label = "TR5: Altamente Sospechoso"
        risk = "> 20% (~35% riesgo de malignidad)"

    dims = nodule_data.get("dimensions", {})
    dim_stats = calculate_nodule_dimensions(
        dims.get("dLongitudinal") or dims.get("d_longitudinal"),
        dims.get("dAnteroposterior") or dims.get("d_anteroposterior"),
        dims.get("dTransverse") or dims.get("d_transverse")
    )

    d_max = dim_stats["max_diameter_cm"]
    d_max_mm = dim_stats["max_diameter_mm"]

    mgmt_code = "NO_ACTION"
    mgmt_text = "No requiere PAAF ni seguimiento ecográfico específico."
    mgmt_badge = "No Requiere PAAF"

    if cat_code == "TR3":
        if d_max >= 2.5:
            mgmt_code = "FNA"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 2.5 cm): Se recomienda PAAF (Biopsia por Aspiración con Aguja Fina)."
            mgmt_badge = "PAAF Indicada"
        elif d_max >= 1.5:
            mgmt_code = "FOLLOWUP"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 1.5 cm): Se recomienda Seguimiento Ecográfico (controles a 1, 3 y 5 años)."
            mgmt_badge = "Seguimiento Ecográfico"
    elif cat_code == "TR4":
        if d_max >= 1.5:
            mgmt_code = "FNA"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 1.5 cm): Se recomienda PAAF (Biopsia por Aspiración con Aguja Fina)."
            mgmt_badge = "PAAF Indicada"
        elif d_max >= 1.0:
            mgmt_code = "FOLLOWUP"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 1.0 cm): Se recomienda Seguimiento Ecográfico (controles a 1, 2, 3 y 5 años)."
            mgmt_badge = "Seguimiento Ecográfico"
    elif cat_code == "TR5":
        if d_max >= 1.0:
            mgmt_code = "FNA"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 1.0 cm): Se recomienda PAAF (Biopsia por Aspiración con Aguja Fina) prioritaria."
            mgmt_badge = "PAAF Prioritaria"
        elif d_max >= 0.5:
            mgmt_code = "FOLLOWUP"
            mgmt_text = f"Nódulo de {d_max_mm} mm (>= 0.5 cm): Se recomienda Seguimiento Ecográfico Anual activo (hasta por 5 años)."
            mgmt_badge = "Seguimiento Anual"

    has_suspicious_lymph = (nodule_data.get("lymphNodes") == "suspicious" or nodule_data.get("lymph_nodes") == "suspicious")
    if has_suspicious_lymph:
        mgmt_text += " Presencia de adenopatía cervical sospechosa: PAAF ganglionar o nodular indicada."
        mgmt_badge = "PAAF Ganglionar"

    return {
        "total_points": total_points,
        "category": {
            "code": cat_code,
            "label": cat_label,
            "malignancy_risk": risk
        },
        "points_breakdown": {
            "composition": {"label": comp_info["label"], "points": comp_pts},
            "echogenicity": {"label": echo_info["label"], "points": echo_pts},
            "shape": {"label": shape_info["label"], "points": shape_pts},
            "margin": {"label": margin_info["label"], "points": margin_pts},
            "foci": {"list": active_foci, "points": foci_pts}
        },
        "dim_stats": dim_stats,
        "management_code": mgmt_code,
        "management_text": mgmt_text,
        "management_badge": mgmt_badge,
        "has_suspicious_lymph_node": has_suspicious_lymph
    }


def generate_tirads_text_report(
    patient_data: Dict[str, Any],
    nodule_data: Dict[str, Any],
    evaluation: Dict[str, Any]
) -> str:
    """
    Genera informe estructurado oficial para RIS/PACS en texto plano.
    """
    date_str = patient_data.get("examDate") or patient_data.get("fecha_estudio") or "2026-09-02"
    dims = evaluation["dim_stats"]
    cat = evaluation["category"]
    pb = evaluation["points_breakdown"]

    loc = nodule_data.get("location", {})
    lobe = loc.get("lobe", "right")
    lobe_str = "Lóbulo Derecho" if lobe == "right" else ("Lóbulo Izquierdo" if lobe == "left" else "Istmo")

    return f"""================================================================================
INFORME DE ECOGRAFÍA TIROIDEA Y ESTRATIFICACIÓN ACR TI-RADS (2017)
CENTRO: {patient_data.get('centerName') or 'Servicio de Diagnóstico por Imágenes'}
================================================================================
PACIENTE: {patient_data.get('name') or 'ANÓNIMO'}
ID / HISTORIA CLÍNICA: {patient_data.get('id') or 'N/A'}
FECHA DEL ESTUDIO: {date_str}
================================================================================
HALLAZGOS ECOGRÁFICOS:
- Ubicación: {lobe_str}.
- Biometría: {dims['summary']}.

DESCRIPTORES ACR TI-RADS:
1. Composición: {pb['composition']['label']} (+{pb['composition']['points']} pts)
2. Ecogenicidad: {pb['echogenicity']['label']} (+{pb['echogenicity']['points']} pts)
3. Forma: {pb['shape']['label']} (+{pb['shape']['points']} pts)
4. Márgenes: {pb['margin']['label']} (+{pb['margin']['points']} pts)
5. Focos: {'; '.join(pb['foci']['list'])} (+{pb['foci']['points']} pts)

PUNTUACIÓN Y CATEGORÍA ACR TI-RADS:
- Puntaje Total: {evaluation['total_points']} puntos.
- Categoría: {cat['label']}.
- Riesgo de Malignidad: {cat['malignancy_risk']}.

CONDUCTA SUGERIDA:
- {evaluation['management_text']}
================================================================================
"""
