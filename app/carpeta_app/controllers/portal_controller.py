"""
Controlador del Portal / Hub Principal de Web-CalcMed
Gestiona el catálogo de calculadoras, búsqueda unificada y configuración institucional.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from carpeta_app.models.database_json import load_settings, save_settings
from carpeta_app.models.estudio_dxa import EstudioDxaModel
from carpeta_app.models.estudio_elastografia import EstudioElastografiaModel
from carpeta_app.models.paciente import PacienteModel

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/")
def index():
    """
    Renderiza el Dashboard principal con accesos directos y los estudios recientes de ambas herramientas.
    """
    settings = load_settings()
    recent_dxa = EstudioDxaModel.list_recent(limit=6)
    recent_elastografia = EstudioElastografiaModel.list_recent(limit=6)

    return render_template(
        "hub.html",
        settings=settings,
        recent_dxa=recent_dxa,
        recent_elastografia=recent_elastografia
    )


@portal_bp.route("/api/pacientes/search")
def search_patients():
    """
    Endpoint JSON para autocompletado rápido y seguro de pacientes existentes.
    """
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    results = PacienteModel.search(query, limit=10)
    return jsonify(results)


@portal_bp.route("/api/settings", methods=["GET", "POST"])
def manage_settings():
    """
    Obtiene o actualiza los ajustes institucionales y del médico radiólogo.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form.to_dict()
        current = load_settings()
        
        # Actualización segura por secciones
        if "nombre_centro" in data:
            current["institucion"]["nombre_centro"] = data.get("nombre_centro", "")
            current["institucion"]["departamento"] = data.get("departamento", "")
            current["institucion"]["direccion"] = data.get("direccion", "")
            current["institucion"]["telefono"] = data.get("telefono", "")
        if "medico_nombre" in data:
            current["medico"]["nombre"] = data.get("medico_nombre", "")
            current["medico"]["especialidad"] = data.get("medico_especialidad", "")
            current["medico"]["matricula"] = data.get("medico_matricula", "")
            current["medico"]["exequatur"] = data.get("medico_exequatur", "")

        success = save_settings(current)
        if request.is_json:
            return jsonify({"success": success, "settings": current})
        flash("Configuración institucional guardada exitosamente.", "success")
        return redirect(url_for("portal.index"))

    return jsonify(load_settings())
