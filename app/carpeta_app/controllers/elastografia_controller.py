"""
Controlador de la Calculadora de Elastografía Hepática Cuantitativa (SWE)
Gestiona 10 mediciones cuantitativas, IQR/Mediana, Baveno VII, Biomarcadores FIB-4 y reportes.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from carpeta_app.models.database_json import load_settings
from carpeta_app.models.paciente import PacienteModel
from carpeta_app.models.estudio_elastografia import EstudioElastografiaModel
from carpeta_app.services.elastografia_calculator import evaluate_elastography
from carpeta_app.services.biomarkers_calculator import calculate_fib4, calculate_apri, calculate_deritis
from carpeta_app.services.report_generator import generate_elastography_report_text

elastografia_bp = Blueprint("elastografia", __name__, url_prefix="/elastografia")


@elastografia_bp.route("/", methods=["GET"])
def form():
    """
    Renderiza el formulario clínico de captura para Elastografía Hepática.
    """
    settings = load_settings()
    return render_template("elastografia/form.html", settings=settings)


@elastografia_bp.route("/api/calculate", methods=["POST"])
def calculate_api():
    """
    Endpoint reactivo JSON para cálculo instantáneo en cliente de IQR, Mediana, Calidad y FIB-4.
    """
    data = request.get_json(silent=True) or {}
    samples = data.get("samples", [])
    unit = data.get("unit", "kPa")
    confounders = data.get("confounders", {})

    eval_res = evaluate_elastography(samples, unit, confounders)

    # Cálculo opcional de biomarcadores
    biomarkers_res = {}
    age = data.get("age")
    ast = data.get("ast")
    alt = data.get("alt")
    platelets = data.get("platelets")
    ast_uln = data.get("ast_uln", 40.0)

    if age and ast and alt and platelets:
        try:
            biomarkers_res["fib4"] = calculate_fib4(int(age), float(ast), float(alt), float(platelets))
            biomarkers_res["apri"] = calculate_apri(float(ast), float(ast_uln), float(platelets))
            biomarkers_res["deritis"] = calculate_deritis(float(ast), float(alt))
        except (ValueError, TypeError):
            pass

    return jsonify({
        "success": True,
        "evaluation": eval_res,
        "biomarkers": biomarkers_res
    })


@elastografia_bp.route("/submit", methods=["POST"])
def submit():
    """
    Procesa el formulario completo de Elastografía Hepática y genera el informe SRU 2020.
    """
    form_data = request.form
    settings = load_settings()

    # 1. Datos del Paciente
    cedula_id = form_data.get("cedula_id", "").strip()
    nombre = form_data.get("nombre", "").strip()
    try:
        edad = int(form_data.get("edad", 45))
    except ValueError:
        edad = 45
    sexo = form_data.get("sexo", "F").strip().upper()
    medico_solicitante = form_data.get("medico_solicitante", "").strip()

    if not cedula_id or not nombre:
        flash("La cédula/ID y el nombre del paciente son campos obligatorios.", "danger")
        return redirect(url_for("elastografia.form"))

    # 2. Contexto Clínico y Factores de Confusión
    indicacion = form_data.get("indicacion", "Evaluación de rigidez / fibrosis hepática").strip()
    etiologia = form_data.get("etiologia", "MASLD/MASH (Esteatosis metabólica)").strip()
    ayuno_adecuado = form_data.get("ayuno_adecuado") == "1"

    confounders = {
        "alt_gt_5x": form_data.get("confounder_alt") == "1",
        "heart_failure": form_data.get("confounder_heart") == "1",
        "biliary_obstruction": form_data.get("confounder_biliary") == "1",
        "fasting_inadequate": not ayuno_adecuado
    }

    # 3. Muestras Cuantitativas (10 mediciones)
    unit = form_data.get("unidad_medicion", "kPa")
    samples = []
    for i in range(1, 11):
        val_str = form_data.get(f"sample_{i}", "").strip()
        try:
            if val_str:
                samples.append(float(val_str))
        except ValueError:
            pass

    # Si se introdujo directamente la mediana e IQR
    if not samples and form_data.get("direct_median"):
        try:
            dir_med = float(form_data.get("direct_median"))
            dir_iqr = float(form_data.get("direct_iqr", 0))
            # Simular muestras representativas para el motor
            samples = [dir_med] * 10
        except ValueError:
            pass

    if not samples:
        flash("Debe ingresar al menos una medición cuantitativa de rigidez.", "danger")
        return redirect(url_for("elastografia.form"))

    evaluation = evaluate_elastography(samples, unit, confounders)

    # 4. Biomarcadores Séricos (Opcional)
    def parse_float(key: str):
        v = form_data.get(key, "").strip()
        try:
            return float(v) if v else None
        except ValueError:
            return None

    ast_val = parse_float("ast_got")
    alt_val = parse_float("alt_gpt")
    plat_val = parse_float("plaquetas")
    ast_uln = parse_float("ast_uln") or 40.0

    tiene_laboratorio = (ast_val is not None and alt_val is not None and plat_val is not None)
    biomarkers_data = {}
    if tiene_laboratorio:
        biomarkers_data["fib4"] = calculate_fib4(edad, ast_val, alt_val, plat_val)
        biomarkers_data["apri"] = calculate_apri(ast_val, ast_uln, plat_val)
        biomarkers_data["deritis"] = calculate_deritis(ast_val, alt_val)

    # 5. Generación del Informe en Texto Plano
    patient_dict = {
        "cedula_id": cedula_id,
        "nombre": nombre,
        "edad": edad,
        "sexo": sexo,
        "medico_solicitante": medico_solicitante
    }
    extra_dict = {
        "indicacion": indicacion,
        "etiologia": etiologia,
        "ayuno_adecuado": ayuno_adecuado,
        "biomarkers": biomarkers_data
    }
    report_text = generate_elastography_report_text(patient_dict, evaluation, settings, extra_dict)

    # 6. Persistencia en SQLite (si no es modo efímero)
    modo_efimero = form_data.get("modo_efimero") == "1"
    estudio_id = None
    if not modo_efimero:
        paciente_id = PacienteModel.get_or_create(
            cedula_id=cedula_id,
            nombre=nombre,
            edad=edad,
            sexo=sexo,
            medico_solicitante=medico_solicitante
        )
        rig = evaluation.get("rigidity", {})
        fib4_obj = biomarkers_data.get("fib4")
        apri_obj = biomarkers_data.get("apri")
        deritis_obj = biomarkers_data.get("deritis")

        estudio_id = EstudioElastografiaModel.create(
            paciente_id=paciente_id,
            indicacion=indicacion,
            etiologia=etiologia,
            ayuno_adecuado=ayuno_adecuado,
            factores_confusion=confounders,
            muestras=samples,
            unidad_medicion=unit,
            mediana_kpa=evaluation.get("median_kpa", 0.0),
            iqr_kpa=evaluation.get("iqr", 0.0),
            ratio_iqr_mediana=evaluation.get("ratio_iqr_mediana_pct", 0.0),
            calidad_tecnica=evaluation.get("quality", {}).get("quality_label", "Satisfactoria"),
            clasificacion_sru=rig.get("stage_label", "Evaluado"),
            riesgo_cacld=rig.get("cacld_risk", "N/A"),
            riesgo_hpcs=rig.get("hpcs_risk", "N/A"),
            tiene_laboratorio=tiene_laboratorio,
            ast_got=ast_val,
            alt_gpt=alt_val,
            plaquetas=plat_val,
            fib4_score=fib4_obj.get("score") if fib4_obj else None,
            fib4_estratificacion=fib4_obj.get("risk_label") if fib4_obj else None,
            apri_score=apri_obj.get("score") if apri_obj else None,
            apri_estratificacion=apri_obj.get("risk_label") if apri_obj else None,
            deritis_ratio=deritis_obj.get("ratio") if deritis_obj else None,
            informe_texto=report_text,
            medico_responsable=settings.get("medico", {}).get("nombre", "Dr. Radiólogo")
        )

    return render_template(
        "elastografia/report_view.html",
        patient=patient_dict,
        extra=extra_dict,
        evaluation=evaluation,
        biomarkers=biomarkers_data,
        report_text=report_text,
        settings=settings,
        estudio_id=estudio_id
    )


@elastografia_bp.route("/view/<int:estudio_id>")
def view_study(estudio_id: int):
    """
    Visualiza un estudio de elastografía guardado históricamente.
    """
    study = EstudioElastografiaModel.get_by_id(estudio_id)
    if not study:
        flash("Estudio no encontrado.", "warning")
        return redirect(url_for("portal.index"))

    settings = load_settings()
    patient_dict = {
        "cedula_id": study["cedula_id"],
        "nombre": study["paciente_nombre"],
        "edad": study["paciente_edad"],
        "sexo": study["paciente_sexo"],
        "medico_solicitante": study["medico_solicitante"]
    }
    evaluation = evaluate_elastography(
        study["muestras"],
        study["unidad_medicion"],
        study["factores_confusion"]
    )
    biomarkers_data = {}
    if study["tiene_laboratorio"]:
        if study.get("fib4_score") is not None:
            biomarkers_data["fib4"] = {
                "score": study["fib4_score"],
                "risk_label": study["fib4_estratificacion"],
                "badge_class": "badge-success" if study["fib4_score"] < 1.3 else ("badge-warning" if study["fib4_score"] <= 2.67 else "badge-danger")
            }
        if study.get("apri_score") is not None:
            biomarkers_data["apri"] = {
                "score": study["apri_score"],
                "risk_label": study["apri_estratificacion"],
                "badge_class": "badge-success" if study["apri_score"] < 0.5 else ("badge-warning" if study["apri_score"] <= 1.0 else "badge-danger")
            }
        if study.get("deritis_ratio") is not None:
            biomarkers_data["deritis"] = {
                "ratio": study["deritis_ratio"],
                "interpretation": f"Ratio: {study['deritis_ratio']}"
            }

    extra_dict = {
        "indicacion": study["indicacion"],
        "etiologia": study["etiologia"],
        "ayuno_adecuado": bool(study["ayuno_adecuado"]),
        "biomarkers": biomarkers_data
    }

    return render_template(
        "elastografia/report_view.html",
        patient=patient_dict,
        extra=extra_dict,
        evaluation=evaluation,
        biomarkers=biomarkers_data,
        report_text=study["informe_texto"],
        settings=settings,
        estudio_id=estudio_id
    )
