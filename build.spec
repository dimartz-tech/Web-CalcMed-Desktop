# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para el ejecutable portable de Web-CalcMed (Windows 11).
# Compilar con: pyinstaller build.spec

import os

block_cipher = None
root = os.path.abspath(os.getcwd())

datas = [
    # El paquete "carpeta_app" se empaqueta como módulo top-level (ver pathex),
    # así que sus datos deben vivir en la raíz del bundle, no bajo "app/".
    (os.path.join(root, "app", "carpeta_app", "views", "templates"), "carpeta_app/views/templates"),
    (os.path.join(root, "app", "carpeta_app", "views", "static"), "carpeta_app/views/static"),
    (os.path.join(root, "app", "databases", "sql", "schema.sql"), "databases/sql"),
    (os.path.join(root, "app", "databases", "config", "default_settings.json"), "databases/config"),
]

a = Analysis(
    ["launcher.py"],
    pathex=[os.path.join(root, "app")],
    binaries=[],
    datas=datas,
    hiddenimports=["carpeta_app", "carpeta_app.controllers", "carpeta_app.models", "carpeta_app.services"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Web-CalcMed-Portable",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
