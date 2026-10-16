"""
Controlador de la Calculadora de Densitometría Ósea (DXA)
Procesa captura clínica, validación ISCD, cálculo evolutivo y renderizado del reporte.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from carpeta_app.models.database_json import load_settings
from carpeta_app.models.paciente import PacienteModel
from carpeta_app.models.estudio_dxa import EstudioDxaModel
from carpeta_app.services.dxa_calculator import (
    calculate_bmi, auto_determine_group, evaluate_iscd, calculate_change, DIAGNOSTIC_GROUPS
)
from carpeta_app.services.report_generator import generate_dxa_report_text

dxa_bp = Blueprint("dxa", __name__, url_prefix="/dxa")


@dxa_bp.route("/", methods=["GET"])
def form():
    """
    Renderiza el formulario clínico de captura para Densitometría Ósea.
    """
    settings = load_settings()
    return render_template("dxa/form.html", settings=settings)


@dxa_bp.route("/api/calculate", methods=["POST"])
def calculate_api():
    """
    Endpoint reactivo JSON para pre-cálculo instantáneo en el frontend.
    """
    payload = request.get_json(silent=True) or {}
    try:
        evaluation = evaluate_iscd(payload)
        return jsonify({"success": True, "evaluation": evaluation})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@dxa_bp.route("/submit", methods=["POST"])
def submit():
    """
    Procesa el formulario completo de DXA, evalúa según normas ISCD y genera el reporte.
    """
    form_data = request.form
    settings = load_settings()

    # 1. Datos del Paciente
    cedula_id = form_data.get("cedula_id", "").strip()
    nombre = form_data.get("nombre", "").strip()
    try:
        edad = int(form_data.get("edad", 50))
    except ValueError:
        edad = 50
    sexo = form_data.get("sexo", "F").strip().upper()
    medico_solicitante = form_data.get("medico_solicitante", "").strip()

    if not cedula_id or not nombre:
        flash("La cédula/ID y el nombre del paciente son campos obligatorios.", "danger")
        return redirect(url_for("dxa.form"))

    # 2. Biometría e IMC
    def parse_float(key: str):
        v = form_data.get(key, "").strip()
        try:
            return float(v) if v else None
        except ValueError:
            return None

    peso_kg = parse_float("peso_kg")
    talla_cm = parse_float("talla_cm")
    imc, cat_imc = calculate_bmi(peso_kg, talla_cm)

    # 3. Factores de Riesgo y Grupo
    is_postmenopausal = form_data.get("es_posmenopausica") == "1"
    group = auto_determine_group(sexo, edad, is_postmenopausal)
    has_fragility_fracture = form_data.get("tiene_fractura_fragilidad") == "1"

    # 4. Mediciones de Sitios Anatómicos
    lumbar_eval = form_data.get("lumbar_eval") == "1"
    lumbar_data = {
        "evaluate": lumbar_eval,
        "region": form_data.get("lumbar_region", "L1-L4"),
        "dmo": parse_float("lumbar_dmo"),
        "t_score": parse_float("lumbar_t_score"),
        "z_score": parse_float("lumbar_z_score"),
        "notes": form_data.get("lumbar_notes", "")
    }

    femur_left_eval = form_data.get("femur_left_eval") == "1"
    femur_left_data = {
        "evaluate": femur_left_eval,
        "neck_dmo": parse_float("femur_left_neck_dmo"),
        "neck_t_score": parse_float("femur_left_neck_t_score"),
        "neck_z_score": parse_float("femur_left_neck_z_score"),
        "total_dmo": parse_float("femur_left_total_dmo"),
        "total_t_score": parse_float("femur_left_total_t_score"),
        "total_z_score": parse_float("femur_left_total_z_score")
    }

    femur_right_eval = form_data.get("femur_right_eval") == "1"
    femur_right_data = {
        "evaluate": femur_right_eval,
        "neck_dmo": parse_float("femur_right_neck_dmo"),
        "neck_t_score": parse_float("femur_right_neck_t_score"),
        "neck_z_score": parse_float("femur_right_neck_z_score"),
        "total_dmo": parse_float("femur_right_total_dmo"),
        "total_t_score": parse_float("femur_right_total_t_score"),
        "total_z_score": parse_float("femur_right_total_z_score")
    }

    radius33_eval = form_data.get("radius33_eval") == "1"
    radius33_data = {
        "evaluate": radius33_eval,
        "side": form_data.get("radius33_side", "No dominante"),
        "dmo": parse_float("radius33_dmo"),
        "t_score": parse_float("radius33_t_score"),
        "z_score": parse_float("radius33_z_score")
    }

    eval_input = {
        "group": group,
        "has_fragility_fracture": has_fragility_fracture,
        "lumbar": lumbar_data,
        "femur_left": femur_left_data,
        "femur_right": femur_right_data,
        "radius33": radius33_data
    }

    evaluation = evaluate_iscd(eval_input)

    # 5. Estudio Previo y Cálculo de LSC
    prev_dmo = parse_float("prev_dmo")
    curr_dmo_evol = lumbar_data["dmo"] or femur_left_data["neck_dmo"] or femur_left_data["total_dmo"]
    comparativa = calculate_change(prev_dmo, curr_dmo_evol) if prev_dmo else None

    # 6. Generación del Informe en Texto Plano
    patient_dict = {
        "cedula_id": cedula_id,
        "nombre": nombre,
        "edad": edad,
        "sexo": sexo,
        "medico_solicitante": medico_solicitante
    }
    extra_dict = {
        "peso_kg": peso_kg,
        "talla_cm": talla_cm,
        "imc": imc,
        "categoria_imc": cat_imc,
        "has_fragility_fracture": has_fragility_fracture,
        "comparativa_evolutiva": comparativa
    }
    report_text = generate_dxa_report_text(patient_dict, evaluation, settings, extra_dict)

    # 7. Persistencia en SQLite (si no es modo efímero)
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
        estudio_id = EstudioDxaModel.create(
            paciente_id=paciente_id,
            peso_kg=peso_kg,
            talla_cm=talla_cm,
            imc=imc,
            categoria_imc=cat_imc,
            grupo_diagnostico=group,
            es_posmenopausica=is_postmenopausal,
            tiene_fractura_fragilidad=has_fragility_fracture,
            datos_mediciones=eval_input,
            diagnostico_global=evaluation.get("global_diagnosis", "Evaluado"),
            score_minimo=evaluation.get("lowest_score"),
            tipo_score_aplicado=evaluation.get("score_type", "T-Score"),
            sitio_critico=evaluation.get("worst_site", "N/A"),
            comparativa_evolutiva=comparativa,
            informe_texto=report_text,
            medico_responsable=settings.get("medico", {}).get("nombre", "Dr. Radiólogo")
        )

    return render_template(
        "dxa/report_view.html",
        patient=patient_dict,
        extra=extra_dict,
        evaluation=evaluation,
        comparativa=comparativa,
        report_text=report_text,
        settings=settings,
        estudio_id=estudio_id
    )


@dxa_bp.route("/view/<int:estudio_id>")
def view_study(estudio_id: int):
    """
    Visualiza un estudio DXA guardado históricamente.
    """
    study = EstudioDxaModel.get_by_id(estudio_id)
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
    evaluation = evaluate_iscd(study["datos_mediciones"])
    extra_dict = {
        "peso_kg": study["peso_kg"],
        "talla_cm": study["talla_cm"],
        "imc": study["imc"],
        "categoria_imc": study["categoria_imc"],
        "has_fragility_fracture": bool(study["tiene_fractura_fragilidad"]),
        "comparativa_evolutiva": study["comparativa_evolutiva"]
    }

    return render_template(
        "dxa/report_view.html",
        patient=patient_dict,
        extra=extra_dict,
        evaluation=evaluation,
        comparativa=study["comparativa_evolutiva"],
        report_text=study["informe_texto"],
        settings=settings,
        estudio_id=estudio_id
    )
