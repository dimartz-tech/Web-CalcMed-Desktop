/**
 * Lógica Reactiva en Cliente para Elastografía Hepática SWE y Biomarcadores (elastografia.js)
 * Calcula en tiempo real Mediana, IQR, Ratio IQR/Mediana %, Confiabilidad SRU y Scores FIB-4/APRI.
 */

document.addEventListener('DOMContentLoaded', () => {
  initLiveElastographyCalculator();
  initBiomarkersCalculator();
});

/* 1. Cálculo de Elastografía (10 mediciones cuantitativas) */
function initLiveElastographyCalculator() {
  const sampleInputs = document.querySelectorAll('.sample-val');
  const unitSelect = document.getElementById('unidad_medicion');

  sampleInputs.forEach(input => {
    input.addEventListener('input', updateElastographyMetrics);
  });
  unitSelect?.addEventListener('change', updateElastographyMetrics);
  updateElastographyMetrics();
}

function updateElastographyMetrics() {
  const sampleInputs = document.querySelectorAll('.sample-val');
  const unit = document.getElementById('unidad_medicion')?.value || 'kPa';

  const samples = [];
  sampleInputs.forEach(inp => {
    const v = parseFloat(inp.value);
    if (!isNaN(v) && v > 0) samples.push(v);
  });

  const medianEl = document.getElementById('live-median');
  const iqrEl = document.getElementById('live-iqr');
  const ratioEl = document.getElementById('live-ratio');
  const qualityBadge = document.getElementById('live-quality-badge');
  const sruBadge = document.getElementById('live-sru-badge');
  const sruDesc = document.getElementById('live-sru-desc');

  if (samples.length === 0) {
    if (medianEl) medianEl.textContent = '---';
    if (iqrEl) iqrEl.textContent = '---';
    if (ratioEl) ratioEl.textContent = '---';
    if (qualityBadge) {
      qualityBadge.className = 'badge badge-neutral';
      qualityBadge.textContent = 'Pendiente de Muestras';
    }
    if (sruBadge) {
      sruBadge.className = 'badge badge-neutral';
      sruBadge.textContent = 'Sin Datos';
    }
    if (sruDesc) sruDesc.textContent = 'Ingrese las mediciones para evaluar la rigidez tisular.';
    return;
  }

  // Ordenar y calcular percentiles
  samples.sort((a, b) => a - b);
  const n = samples.length;

  function getPercentile(p) {
    const k = (n - 1) * p;
    const f = Math.floor(k);
    const c = Math.ceil(k);
    if (f === c) return samples[k];
    return samples[f] * (c - k) + samples[c] * (k - f);
  }

  const median = getPercentile(0.5);
  const q1 = getPercentile(0.25);
  const q3 = getPercentile(0.75);
  const iqr = q3 - q1;
  const ratioPct = median > 0 ? (iqr / median) * 100 : 0;

  if (medianEl) medianEl.textContent = `${median.toFixed(1)} ${unit}`;
  if (iqrEl) iqrEl.textContent = `${iqr.toFixed(1)} ${unit}`;
  if (ratioEl) ratioEl.textContent = `${ratioPct.toFixed(1)}%`;

  // Criterio de Calidad Técnica
  const maxThreshold = unit.toLowerCase() === 'kpa' ? 30.0 : 15.0;
  const isSatisfactory = ratioPct <= maxThreshold;

  if (qualityBadge) {
    if (isSatisfactory) {
      qualityBadge.className = 'badge badge-success';
      qualityBadge.textContent = `✓ Calidad Satisfactoria (≤ ${maxThreshold}%)`;
    } else {
      qualityBadge.className = 'badge badge-danger';
      qualityBadge.textContent = `⚠ Variabilidad Excesiva (> ${maxThreshold}%)`;
    }
  }

  // Clasificación SRU 2020 (Regla de 4)
  const medianKpa = unit.toLowerCase() === 'kpa' ? median : 3 * Math.pow(median, 2);

  if (sruBadge && sruDesc) {
    if (medianKpa <= 5.0) {
      sruBadge.className = 'badge badge-success';
      sruBadge.textContent = 'NORMAL (≤ 5.0 kPa)';
      sruDesc.textContent = 'Parénquima hepático normal. Alta probabilidad de descartar fibrosis clínicamente significativa.';
    } else if (medianKpa < 9.0) {
      sruBadge.className = 'badge badge-info';
      sruBadge.textContent = 'DESCARTE cACLD (< 9.0 kPa)';
      sruDesc.textContent = 'Enfermedad Hepática Crónica Avanzada Compensada descartada con alta certeza.';
    } else if (medianKpa <= 13.0) {
      sruBadge.className = 'badge badge-warning';
      sruBadge.textContent = 'ZONA GRIS (9.0 - 13.0 kPa)';
      sruDesc.textContent = 'Sugestivo de fibrosis avanzada o cACLD. Requiere correlación obligatoria con FIB-4 o biopsia.';
    } else if (medianKpa <= 17.0) {
      sruBadge.className = 'badge badge-danger';
      sruBadge.textContent = 'cACLD ESTABLECIDO (> 13.0 kPa)';
      sruDesc.textContent = 'Alta probabilidad de fibrosis avanzada severa / cirrosis compensada (F3-F4).';
    } else {
      sruBadge.className = 'badge badge-danger';
      sruBadge.textContent = 'ALTO RIESGO HPCS (> 17.0 kPa)';
      sruDesc.textContent = 'Alta probabilidad de Hipertensión Portal Clínicamente Significativa (Criterios Baveno VII).';
    }
  }
}

/* 2. Cálculo Reactivo de Biomarcadores Séricos (FIB-4 / APRI) */
function initBiomarkersCalculator() {
  const inputs = ['edad', 'ast_got', 'alt_gpt', 'plaquetas', 'ast_uln'];
  inputs.forEach(id => {
    document.getElementById(id)?.addEventListener('input', updateBiomarkersMetrics);
  });
  updateBiomarkersMetrics();
}

function updateBiomarkersMetrics() {
  const edad = parseInt(document.getElementById('edad')?.value || '45', 10);
  const ast = parseFloat(document.getElementById('ast_got')?.value);
  const alt = parseFloat(document.getElementById('alt_gpt')?.value);
  const plat = parseFloat(document.getElementById('plaquetas')?.value);
  const astUln = parseFloat(document.getElementById('ast_uln')?.value) || 40.0;

  const fib4ScoreEl = document.getElementById('live-fib4-score');
  const fib4BadgeEl = document.getElementById('live-fib4-badge');
  const apriScoreEl = document.getElementById('live-apri-score');
  const apriBadgeEl = document.getElementById('live-apri-badge');

  if (!ast || !alt || !plat || ast <= 0 || alt <= 0 || plat <= 0 || edad <= 0) {
    if (fib4ScoreEl) fib4ScoreEl.textContent = '---';
    if (fib4BadgeEl) {
      fib4BadgeEl.className = 'badge badge-neutral';
      fib4BadgeEl.textContent = 'Pendiente de Lab';
    }
    if (apriScoreEl) apriScoreEl.textContent = '---';
    if (apriBadgeEl) {
      apriBadgeEl.className = 'badge badge-neutral';
      apriBadgeEl.textContent = 'Pendiente de Lab';
    }
    return;
  }

  // 1. FIB-4 = (Edad * AST) / (Plaquetas * sqrt(ALT))
  const fib4 = (edad * ast) / (plat * Math.sqrt(alt));
  if (fib4ScoreEl) fib4ScoreEl.textContent = fib4.toFixed(2);

  const lowCutoff = edad >= 65 ? 2.0 : 1.30;
  if (fib4BadgeEl) {
    if (fib4 < lowCutoff) {
      fib4BadgeEl.className = 'badge badge-success';
      fib4BadgeEl.textContent = 'Bajo Riesgo (F0-F1)';
    } else if (fib4 <= 2.67) {
      fib4BadgeEl.className = 'badge badge-warning';
      fib4BadgeEl.textContent = 'Riesgo Indeterminado (F2)';
    } else {
      fib4BadgeEl.className = 'badge badge-danger';
      fib4BadgeEl.textContent = 'Alto Riesgo (F3-F4)';
    }
  }

  // 2. APRI = ((AST / LSN_AST) * 100) / Plaquetas
  const apri = ((ast / astUln) * 100) / plat;
  if (apriScoreEl) apriScoreEl.textContent = apri.toFixed(2);

  if (apriBadgeEl) {
    if (apri < 0.50) {
      apriBadgeEl.className = 'badge badge-success';
      apriBadgeEl.textContent = 'Bajo Riesgo';
    } else if (apri <= 1.00) {
      apriBadgeEl.className = 'badge badge-warning';
      apriBadgeEl.textContent = 'Riesgo Intermedio';
    } else {
      apriBadgeEl.className = 'badge badge-danger';
      apriBadgeEl.textContent = 'Alto Riesgo / F3-F4';
    }
  }
}
