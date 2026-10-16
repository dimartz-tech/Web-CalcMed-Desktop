# Web-CalcMed — Edición Portable (Windows 11)

Proyecto independiente que empaqueta el backend Flask de
[Web-CalcMed](../Web-CalcMed) como un único ejecutable `.exe` portable para
Windows 11, sin necesidad de instalar Python, Node ni dependencias en la
máquina destino.

## Cómo funciona

- `launcher.py` arranca el servidor Flask embebido (`app/carpeta_app`) en
  `127.0.0.1:5000` y abre el navegador predeterminado automáticamente.
- La base de datos SQLite y la configuración institucional (médico, equipo)
  se guardan en una carpeta `data/` creada junto al `.exe`, nunca dentro del
  propio ejecutable. Esto permite copiar el `.exe` + `data/` a una memoria
  USB y conservar los datos.
- `build.spec` es la definición de PyInstaller usada para compilar el
  ejecutable en modo "un solo archivo".

## Obtener el .exe sin compilar nada localmente

Este repo incluye un workflow de GitHub Actions
(`.github/workflows/build-windows.yml`) que compila el `.exe` en un runner
Windows real cada vez que se hace push a `main`, o manualmente desde la
pestaña **Actions → Build Windows Portable EXE → Run workflow**.

1. Sube este repositorio a GitHub.
2. Ve a la pestaña **Actions** y espera a que termine el job `build`.
3. Descarga el artifact `Web-CalcMed-Portable-Windows`: contiene
   `Web-CalcMed-Portable.exe`.
4. Copia el `.exe` a cualquier carpeta en Windows 11 y ejecútalo.

## Compilar manualmente en una máquina Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller build.spec
```

El ejecutable resultante queda en `dist\Web-CalcMed-Portable.exe`.

## Actualizar esta edición portable

Este proyecto mantiene una **copia independiente** del backend
(`app/carpeta_app` y `app/databases`), tomada de `Web-CalcMed/proyecto`. Si el
proyecto web original cambia, hay que volver a copiar esos archivos aquí
(no hay sincronización automática — es intencional, para mantener este
empaquetado como un proyecto aparte).
