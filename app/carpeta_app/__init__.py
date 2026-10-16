"""
Application Factory de Web-CalcMed
Configura Flask, inicializa la base de datos SQLite, registra Blueprints e inyecta cabeceras de seguridad HTTP.
"""

import os
from flask import Flask
from carpeta_app.models.database_sql import init_db


def create_app() -> Flask:
    """
    Crea y configura la instancia de la aplicación Flask.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "views", "templates")
    static_dir = os.path.join(base_dir, "views", "static")

    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir
    )

    # Clave secreta para mensajes flash y sesiones seguras
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "calcmed_secure_secret_key_2026_radiology")

    # Inicializar base de datos relacional
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            print(f"[ADVERTENCIA] Error inicializando base de datos SQLite: {e}")

    # Registro de Blueprints modulares
    from carpeta_app.controllers.portal_controller import portal_bp
    from carpeta_app.controllers.dxa_controller import dxa_bp
    from carpeta_app.controllers.elastografia_controller import elastografia_bp
    from carpeta_app.controllers.reportes_controller import reportes_bp

    app.register_blueprint(portal_bp)
    app.register_blueprint(dxa_bp)
    app.register_blueprint(elastografia_bp)
    app.register_blueprint(reportes_bp)

    # Inyección de cabeceras HTTP de seguridad (Security-by-Design)
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "object-src 'none';"
        )
        return response

    return app

# Alias en español por compatibilidad
crear_app = create_app
