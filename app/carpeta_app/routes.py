import os
import json
from flask import send_from_directory, jsonify, request, current_app

def registrar_rutas(app):
    dist_dir = app.config.get('DIST_DIR')
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'databases', 'config'))
    os.makedirs(config_dir, exist_ok=True)

    @app.route('/')
    def index():
        if os.path.exists(os.path.join(dist_dir, 'index.html')):
            return send_from_directory(dist_dir, 'index.html')
        return "Web-CalcMed Backend Activo. Ejecuta 'pnpm build' para compilar la interfaz gráfica.", 200

    @app.route('/api/health')
    def health():
        return jsonify({
            "status": "ok",
            "app": "Web-CalcMed",
            "version": "0.1.0",
            "tools": [
                "Densitometria Osea (ISCD)",
                "Elastografia Hepatica (SRU 2020)",
                "Ecografia Tiroidea (ACR TI-RADS 2017)"
            ]
        })

    @app.route('/api/config/doctor', methods=['GET', 'POST'])
    def config_doctor():
        doc_path = os.path.join(config_dir, 'doctor_config.json')
        if request.method == 'POST':
            data = request.get_json() or {}
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "saved", "data": data})
        
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({
            "reporting_doctor": "Dra. Elena Vargas",
            "specialty": "Radióloga",
            "license_number": "M.P. 45892",
            "institution": "Centro de Diagnóstico Médico"
        })

    @app.route('/api/config/equipment', methods=['GET', 'POST'])
    def config_equipment():
        eq_path = os.path.join(config_dir, 'equipment_config.json')
        if request.method == 'POST':
            data = request.get_json() or {}
            with open(eq_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "saved", "data": data})
        
        if os.path.exists(eq_path):
            with open(eq_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({
            "brand_model": "GE Logiq E10 / Hologic Horizon W",
            "serial_number": "SN-2026-99",
            "center_name": "Centro Médico Especializado"
        })

    @app.route('/<path:filename>')
    def serve_static(filename):
        if dist_dir and os.path.exists(os.path.join(dist_dir, filename)):
            return send_from_directory(dist_dir, filename)
        return "Archivo no encontrado", 404

