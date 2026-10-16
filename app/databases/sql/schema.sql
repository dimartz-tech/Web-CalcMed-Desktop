-- ==============================================================================
-- Web-CalcMed: Esquema Relacional de Base de Datos SQLite (calcmed.db)
-- Integridad Referencial forzada con 'PRAGMA foreign_keys = ON;'
-- ==============================================================================

-- 1. Tabla de Pacientes (Unificada para todas las calculadoras)
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula_id TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    edad INTEGER NOT NULL CHECK (edad >= 0 AND edad <= 125),
    sexo TEXT NOT NULL CHECK (sexo IN ('M', 'F')),
    telefono TEXT,
    medico_solicitante TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Estudios de Densitometría Ósea (DXA)
CREATE TABLE IF NOT EXISTS estudios_dxa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha_estudio DATE NOT NULL DEFAULT CURRENT_DATE,
    peso_kg REAL,
    talla_cm REAL,
    imc REAL,
    categoria_imc TEXT,
    grupo_diagnostico TEXT NOT NULL, -- postmenopausal, man_50_plus, premenopausal, man_under_50
    es_posmenopausica INTEGER DEFAULT 1,
    tiene_fractura_fragilidad INTEGER DEFAULT 0,
    datos_mediciones_json TEXT NOT NULL, -- Datos de columna L1-L4, fémur izq/der, radio 33%
    diagnostico_global TEXT NOT NULL, -- Normal, Osteopenia, Osteoporosis, Osteoporosis Severa, etc.
    score_minimo REAL,
    tipo_score_aplicado TEXT NOT NULL, -- T-Score o Z-Score
    sitio_critico TEXT,
    comparativa_evolutiva_json TEXT, -- LSC, delta DMO, % delta
    informe_texto TEXT,
    medico_responsable TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

-- 3. Tabla de Estudios de Elastografía Hepática (SWE)
CREATE TABLE IF NOT EXISTS estudios_elastografia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    fecha_estudio DATE NOT NULL DEFAULT CURRENT_DATE,
    indicacion TEXT,
    etiologia TEXT,
    ayuno_adecuado INTEGER DEFAULT 1,
    factores_confusion_json TEXT, -- transaminasas > 5x, falla cardiaca, etc.
    muestras_json TEXT NOT NULL, -- Array de 10 mediciones cuantitativas
    unidad_medicion TEXT NOT NULL DEFAULT 'kPa', -- 'kPa' o 'm/s'
    mediana_kpa REAL NOT NULL,
    iqr_kpa REAL NOT NULL,
    ratio_iqr_mediana REAL NOT NULL,
    calidad_tecnica TEXT NOT NULL, -- 'Satisfactoria' o 'No Confiable'
    clasificacion_sru TEXT NOT NULL, -- 'Normal', 'Descarte cACLD', 'Zona Gris', 'cACLD', 'HPCS'
    riesgo_cacld TEXT,
    riesgo_hpcs TEXT,
    -- Módulo de Biomarcadores Séricos
    tiene_laboratorio INTEGER DEFAULT 0,
    ast_got REAL,
    alt_gpt REAL,
    plaquetas REAL,
    fib4_score REAL,
    fib4_estratificacion TEXT,
    apri_score REAL,
    apri_estratificacion TEXT,
    deritis_ratio REAL,
    informe_texto TEXT,
    medico_responsable TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
);

-- Índices de búsqueda optimizada
CREATE INDEX IF NOT EXISTS idx_pacientes_cedula ON pacientes (cedula_id);
CREATE INDEX IF NOT EXISTS idx_pacientes_nombre ON pacientes (nombre);
CREATE INDEX IF NOT EXISTS idx_dxa_paciente ON estudios_dxa (paciente_id);
CREATE INDEX IF NOT EXISTS idx_elastografia_paciente ON estudios_elastografia (paciente_id);
