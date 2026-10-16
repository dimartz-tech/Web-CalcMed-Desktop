"""
Punto de entrada del ejecutable portable de Web-CalcMed para Windows.

Arranca el servidor Flask embebido, resuelve una carpeta de datos escribible
junto al .exe (para que la base de datos y la configuración viajen con el
ejecutable, sin tocar el sistema) y abre el navegador predeterminado.
"""

import os
import sys
import threading
import time
import webbrowser


def resource_base_dir() -> str:
    """Carpeta donde PyInstaller extrae el código y los recursos de solo lectura."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def executable_dir() -> str:
    """Carpeta donde vive el .exe (o este script en modo desarrollo)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    base_dir = resource_base_dir()
    sys.path.insert(0, os.path.join(base_dir, "app"))

    data_dir = os.path.join(executable_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    os.environ["WEBCALCMED_DATA_DIR"] = data_dir

    from carpeta_app import crear_app

    app = crear_app()

    port = 5000
    url = f"http://127.0.0.1:{port}"

    def abrir_navegador():
        time.sleep(1.0)
        webbrowser.open(url)

    threading.Thread(target=abrir_navegador, daemon=True).start()

    print("=" * 60)
    print("Web-CalcMed - Edicion Portable para Windows")
    print(f"Datos locales guardados en: {data_dir}")
    print(f"Interfaz disponible en: {url}")
    print("Cierra esta ventana para detener la aplicacion.")
    print("=" * 60)

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
