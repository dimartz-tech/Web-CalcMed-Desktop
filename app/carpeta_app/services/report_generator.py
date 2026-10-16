"""
Generador de Reportes Médicos Estructurados en Texto Plano para RIS/PACS/EMR
Ensambla los informes clínicos de Densitometría Ósea (ISCD) y Elastografía Hepática (US-E-14.0 / SRU 2020).
"""

from typing import Dict, Any, Optional


def generate_dxa_report_text(patient: Dict[str, Any], evaluation: Dict[str, Any], settings: Dict[str, Any], extra: Dict[str, Any]) -> str:
    """
    Genera el informe estructurado de Densitometría Ósea en texto plano listo para copiar a RIS/PACS.
    """
    inst = settings.get("institucion", {})
    doc = settings.get("medico", {})

    lines = []
    lines.append("================================================================================")
    lines.append(f"{inst.get('nombre_centro', 'CENTRO DE DIAGNÓSTICO MÉDICO').upper()}")
    lines.append(f"{inst.get('departamento', 'DEPARTAMENTO DE RADIOLOGÍA Y DENSITOMETRÍA ÓSEA').upper()}")
    lines.append("INFORME DE DENSITOMETRÍA ÓSEA (DXA) - GUÍAS OFICIALES ISCD")
    lines.append("================================================================================")
    lines.append("")
    lines.append("DATOS DEL PACIENTE Y ESTUDIO:")
    lines.append(f"- Paciente: {patient.get('nombre', 'N/A')}")
    lines.append(f"- Cédula / ID: {patient.get('cedula_id', 'N/A')}")
    lines.append(f"- Edad: {patient.get('edad', 'N/A')} años | Sexo: {'Femenino' if patient.get('sexo') == 'F' else 'Masculino'}")
    if patient.get("medico_solicitante"):
        lines.append(f"- Médico Solicitante: {patient.get('medico_solicitante')}")

    peso = extra.get("peso_kg")
    talla = extra.get("talla_cm")
    imc = extra.get("imc")
    cat_imc = extra.get("categoria_imc")
    if peso and talla and imc:
        lines.append(f"- Biometría: Peso {peso} kg | Talla {talla} cm | IMC {imc} kg/m² ({cat_imc})")

    group_label = "Mujer Posmenopáusica" if evaluation.get("is_adult") and patient.get("sexo") == 'F' else (
        "Hombre ≥ 50 años" if evaluation.get("is_adult") else (
            "Mujer Premenopáusica" if patient.get("sexo") == 'F' else "Hombre < 50 años"
        )
    )
    score_used = evaluation.get("score_type", "T-Score")
    lines.append(f"- Grupo Diagnóstico: {group_label} (Criterio aplicado: {score_used})")
    if extra.get("has_fragility_fracture"):
        lines.append("- Antecedente de fractura por fragilidad previa: SÍ (Factor de riesgo mayor)")

    lines.append("")
    lines.append("TÉCNICA DE EXPLORACIÓN:")
    lines.append("- Densitometría Ósea por Absorciometría de Rayos X de Doble Energía (DXA) con haz en abanico.")
    lines.append("  Evaluación estandarizada según las recomendaciones de la International Society for Clinical Densitometry (ISCD).")

    lines.append("")
    lines.append("RESULTADOS DENSITOMÉTRICOS:")
    lines.append(f"{'Región Anatómica':<32} | {'DMO (g/cm²)':<12} | {'T-Score':<8} | {'Z-Score':<8} | {'Diagnóstico Parcial'}")
    lines.append("-" * 80)

    for site in evaluation.get("sites", []):
        name = site.get("name", "N/A")
        dmo_str = f"{site.get('dmo'):.3f}" if site.get("dmo") is not None else "---"
        t_str = f"{site.get('t_score'):+.1f}" if site.get("t_score") is not None else "---"
        z_str = f"{site.get('z_score'):+.1f}" if site.get("z_score") is not None else "---"
        
        diag_part = site.get("t_category", {}).get("label") if evaluation.get("is_adult") and site.get("t_category") else (
            site.get("z_category", {}).get("label") if site.get("z_category") else "Evaluado"
        )
        lines.append(f"{name:<32} | {dmo_str:<12} | {t_str:<8} | {z_str:<8} | {diag_part}")

    # Análisis evolutivo si existe
    evol = extra.get("comparativa_evolutiva")
    if evol:
        lines.append("")
        lines.append("ANÁLISIS COMPARATIVO EVOLUTIVO:")
        lines.append(f"- Variación absoluta de DMO: {evol.get('delta_abs', 0):+.4f} g/cm² ({evol.get('delta_pct', 0):+.2f}%)")
        lines.append(f"- Interpretación estadística: {evol.get('interpretation', '')}")

    lines.append("")
    lines.append("IMPRESIÓN DIAGNÓSTICA (CRITERIO ISCD):")
    lines.append(f"1. {evaluation.get('global_diagnosis', 'No concluyente').upper()}.")
    if evaluation.get("lowest_score") is not None:
        lines.append(f"   (Valor mínimo registrado: {score_used} {evaluation.get('lowest_score'):+.1f} en {evaluation.get('worst_site')}).")
    
    lines.append("")
    lines.append("RECOMENDACIONES GENERALES:")
    lines.append("- Correlación con factores de riesgo clínicos de fractura (herramienta FRAX).")
    lines.append("- Mantener ingesta óptima de Calcio y Vitamina D según criterio médico tratante.")
    lines.append("- Control densitométrico evolutivo según protocolo clínico en 1 a 2 años en el mismo equipo.")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"MÉDICO RESPONSABLE: {doc.get('nombre', 'Dr. Radiólogo')} | Matrícula: {doc.get('matricula', '')}")
    lines.append(f"{doc.get('especialidad', '')}")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_elastography_report_text(patient: Dict[str, Any], evaluation: Dict[str, Any], settings: Dict[str, Any], extra: Dict[str, Any]) -> str:
    """
    Genera el informe estructurado de Elastografía Hepática en texto plano según plantilla US-E-14.0 y Consenso SRU 2020.
    """
    inst = settings.get("institucion", {})
    doc = settings.get("medico", {})
    rigidity = evaluation.get("rigidity", {})
    quality = evaluation.get("quality", {})

    lines = []
    lines.append("================================================================================")
    lines.append(f"{inst.get('nombre_centro', 'CENTRO DE DIAGNÓSTICO MÉDICO').upper()}")
    lines.append("DEPARTAMENTO DE ULTRASONIDO Y ECOGRAFÍA CUANTITATIVA")
    lines.append("INFORME DE ELASTOGRAFÍA HEPÁTICA POR ONDAS DE CHOQUE (SWE)")
    lines.append("CÓDIGO INSTITUCIONAL: US-E-14.0 | CONSENSO SRU 2020")
    lines.append("================================================================================")
    lines.append("")
    lines.append("DATOS DEL PACIENTE Y ESTUDIO:")
    lines.append(f"- Paciente: {patient.get('nombre', 'N/A')}")
    lines.append(f"- Cédula / ID: {patient.get('cedula_id', 'N/A')}")
    lines.append(f"- Edad: {patient.get('edad', 'N/A')} años | Sexo: {'Femenino' if patient.get('sexo') == 'F' else 'Masculino'}")
    if patient.get("medico_solicitante"):
        lines.append(f"- Médico Solicitante: {patient.get('medico_solicitante')}")
    if extra.get("indicacion"):
        lines.append(f"- Indicación Clínica: {extra.get('indicacion')}")
    if extra.get("etiologia"):
        lines.append(f"- Etiología de Base: {extra.get('etiologia')}")

    lines.append("")
    lines.append("TÉCNICA DE EXPLORACIÓN / PROTOCOLO:")
    lines.append("- Muestreo cuantitativo de la rigidez hepática mediante Shear Wave Elastography (SWE)")
    lines.append("  en lóbulo hepático derecho (segmentos VII/VIII), con transductor convexo multifrecuencia,")
    lines.append("  paciente en decúbito y apnea espiratoria neutra, tras ayuno adecuado ≥ 4-6 horas.")
    lines.append(f"- Mediciones válidas adquiridas: {evaluation.get('sample_count', 10)} muestras independientes.")

    lines.append("")
    lines.append("CRITERIOS DE CALIDAD TÉCNICA (SRU 2020 / WFUMB):")
    lines.append(f"- Mediana de Rigidez Hepática (LSM): {evaluation.get('median_kpa', 0.0):.1f} kPa")
    lines.append(f"- Rango Intercuartílico (IQR): {evaluation.get('iqr', 0.0):.1f} kPa")
    lines.append(f"- Ratio IQR / Mediana: {evaluation.get('ratio_iqr_mediana_pct', 0.0):.1f}% (Criterio de calidad: {quality.get('quality_label')})")

    # Alertas de confusión si aplican
    alerts = evaluation.get("confounder_alerts", [])
    if alerts:
        lines.append("- Advertencias técnicas de correlación:")
        for al in alerts:
            lines.append(f"  * {al}")

    # Biomarcadores séricos si fueron provistos
    biomarkers = extra.get("biomarkers")
    if biomarkers and biomarkers.get("fib4"):
        fib4 = biomarkers.get("fib4")
        apri = biomarkers.get("apri")
        deritis = biomarkers.get("deritis")
        lines.append("")
        lines.append("BIOMARCADORES SÉRICOS COMPLEMENTARIOS:")
        lines.append(f"- Score FIB-4: {fib4.get('score'):.2f} -> {fib4.get('risk_label')}")
        if apri:
            lines.append(f"- Score APRI: {apri.get('score'):.2f} -> {apri.get('risk_label')}")
        if deritis:
            lines.append(f"- Ratio AST/ALT (De Ritis): {deritis.get('ratio'):.2f} ({deritis.get('interpretation')})")

    lines.append("")
    lines.append("IMPRESIÓN DIAGNÓSTICA (CONSENSO SRU 2020 / REGLA DE CUATRO):")
    stage_txt = rigidity.get('stage_label', '').upper().replace("CACLD", "cACLD")
    lines.append(f"2. MEDIANA DE RIGIDEZ HEPÁTICA DE {evaluation.get('median_kpa', 0.0):.1f} kPa: {stage_txt}.")
    lines.append(f"   - Estratificación cACLD: {rigidity.get('cacld_risk', 'N/A')}")
    lines.append(f"   - Riesgo de Hipertensión Portal (Baveno VII): {rigidity.get('hpcs_risk', 'N/A')}")

    lines.append("")
    lines.append("RECOMENDACIÓN CLÍNICA:")
    lines.append(f"- {rigidity.get('recommendation', '')}")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"MÉDICO RESPONSABLE: {doc.get('nombre', 'Dr. Radiólogo')} | Matrícula: {doc.get('matricula', '')}")
    lines.append(f"{doc.get('especialidad', '')}")
    lines.append("=" * 80)

    return "\n".join(lines)
