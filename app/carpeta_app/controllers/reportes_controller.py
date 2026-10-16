"""
Controlador de Exportación y Descarga de Reportes Médicos
Proporciona endpoints para descarga en archivo de texto plano y vista directa de impresión.
"""

from flask import Blueprint, Response, request, abort
from carpeta_app.models.estudio_dxa import EstudioDxaModel
from carpeta_app.models.estudio_elastografia import EstudioElastografiaModel

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@reportes_bp.route("/download/<tipo>/<int:estudio_id>")
def download_txt(tipo: str, estudio_id: int):
    """
    Descarga el informe médico estructurado en un archivo .txt plano.
    """
    if tipo == "dxa":
        study = EstudioDxaModel.get_by_id(estudio_id)
        prefix = "DXA"
    elif tipo == "elastografia":
        study = EstudioElastografiaModel.get_by_id(estudio_id)
        prefix = "SWE"
    else:
        abort(404)

    if not study or not study.get("informe_texto"):
        abort(404)

    cedula = study.get("cedula_id", "sin_id").replace(" ", "_")
    filename = f"Informe_{prefix}_{cedula}_{study.get('fecha_estudio', 'hoy')}.txt"

    return Response(
        study["informe_texto"],
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
