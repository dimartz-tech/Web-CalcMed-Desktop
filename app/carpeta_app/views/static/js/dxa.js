/**
 * Lógica Reactiva en Cliente para Densitometría Ósea DXA (dxa.js)
 * Portado y adaptado de iscdCalculator.js para pre-evaluación instantánea sin recarga.
 */

document.addEventListener('DOMContentLoaded', () => {
  initBmiCalculator();
  initSectionToggles();
  initLiveDxaEvaluation();
});

/* 1. Cálculo Reactivo de IMC */
function initBmiCalculator() {
  const pesoInput = document.getElementById('peso_kg');
  const tallaInput = document.getElementById('talla_cm');
  const imcBadge = document.getElementById('imc_badge');

  function updateBMI() {
    const peso = parseFloat(pesoInput?.value);
    const talla = parseFloat(tallaInput?.value);

    if (peso > 0 && talla > 0 && imcBadge) {
      const hM = talla / 100;
      const bmi = (peso / (hM * hM)).toFixed(1);
      let cat = 'Normopeso';
      if (bmi < 18.5) cat = 'Bajo peso';
      else if (bmi >= 30.0) cat = 'Obesidad';
      else if (bmi >= 25.0) cat = 'Sobrepeso';

      imcBadge.textContent = `IMC: ${bmi} kg/m² (${cat})`;
      imcBadge.style.display = 'inline-flex';
    } else if (imcBadge) {
      imcBadge.style.display = 'none';
    }
  }

  pesoInput?.addEventListener('input', updateBMI);
  tallaInput?.addEventListener('input', updateBMI);
}

/* 2. Activar / Desactivar Secciones Anatómicas */
function initSectionToggles() {
  const toggles = [
    { check: 'lumbar_eval', panel: 'lumbar_panel' },
    { check: 'femur_left_eval', panel: 'femur_left_panel' },
    { check: 'femur_right_eval', panel: 'femur_right_panel' },
    { check: 'radius33_eval', panel: 'radius33_panel' }
  ];

  toggles.forEach(({ check, panel }) => {
    const cb = document.getElementById(check);
    const p = document.getElementById(panel);
    if (cb && p) {
      cb.addEventListener('change', () => {
        p.style.opacity = cb.checked ? '1' : '0.4';
        p.querySelectorAll('input, select').forEach(i => {
          if (i !== cb) i.disabled = !cb.checked;
        });
        triggerLiveEvaluation();
      });
    }
  });
}

/* 3. Pre-evaluación Diagnóstica en Vivo */
function initLiveDxaEvaluation() {
  const inputs = document.querySelectorAll('#dxa-form input, #dxa-form select');
  inputs.forEach(input => {
    input.addEventListener('input', triggerLiveEvaluation);
    input.addEventListener('change', triggerLiveEvaluation);
  });
  triggerLiveEvaluation();
}

function triggerLiveEvaluation() {
  const edad = parseInt(document.getElementById('edad')?.value || '50', 10);
  const sexo = document.getElementById('sexo')?.value || 'F';
  const isPost = document.getElementById('es_posmenopausica')?.checked ?? true;
  const hasFracture = document.getElementById('tiene_fractura_fragilidad')?.checked ?? false;

  const isAdult = (sexo === 'F' && (isPost || edad >= 50)) || (sexo === 'M' && edad >= 50);

  // Recolectar T-Scores válidos
  const scores = [];
  const addScore = (val, name) => {
    const num = parseFloat(val);
    if (!isNaN(num)) scores.push({ val: num, name });
  };

  if (document.getElementById('lumbar_eval')?.checked) {
    addScore(document.getElementById('lumbar_t_score')?.value, 'Columna Lumbar');
  }
  if (document.getElementById('femur_left_eval')?.checked) {
    addScore(document.getElementById('femur_left_neck_t_score')?.value, 'Cuello Femoral Izq.');
    addScore(document.getElementById('femur_left_total_t_score')?.value, 'Fémur Total Izq.');
  }
  if (document.getElementById('femur_right_eval')?.checked) {
    addScore(document.getElementById('femur_right_neck_t_score')?.value, 'Cuello Femoral Der.');
    addScore(document.getElementById('femur_right_total_t_score')?.value, 'Fémur Total Der.');
  }
  if (document.getElementById('radius33_eval')?.checked) {
    addScore(document.getElementById('radius33_t_score')?.value, 'Radio 33%');
  }

  const liveBadge = document.getElementById('live-dxa-badge');
  const liveDesc = document.getElementById('live-dxa-desc');

  if (scores.length === 0) {
    if (liveBadge) {
      liveBadge.className = 'badge badge-neutral';
      liveBadge.textContent = 'Pendiente de Mediciones';
    }
    if (liveDesc) liveDesc.textContent = 'Ingrese los valores de DMO o T-Score para previsualizar el diagnóstico.';
    return;
  }

  const minScore = scores.reduce((min, s) => s.val < min.val ? s : min, scores[0]);

  if (isAdult) {
    if (minScore.val >= -1.0) {
      setLiveBadge('NORMAL', 'badge-success', `Densidad mineral ósea normal (T-Score mínimo: ${minScore.val.toFixed(1)} en ${minScore.name}).`);
    } else if (minScore.val > -2.5) {
      setLiveBadge('OSTEOPENIA (Masa Ósea Baja)', 'badge-warning', `Masa ósea baja (-2.5 < T-Score < -1.0) en ${minScore.name}.`);
    } else {
      if (hasFracture) {
        setLiveBadge('OSTEOPOROSIS SEVERA', 'badge-danger', `Osteoporosis establecida con fractura por fragilidad previa (T-Score ${minScore.val.toFixed(1)} en ${minScore.name}).`);
      } else {
        setLiveBadge('OSTEOPOROSIS', 'badge-danger', `Osteoporosis (T-Score ≤ -2.5) en ${minScore.name}.`);
      }
    }
  } else {
    // Grupo Joven / Premenopáusico (Z-Score)
    if (minScore.val > -2.0) {
      setLiveBadge('DENTRO DEL RANGO ESPERADO', 'badge-success', `Z-Score > -2.0 en ${minScore.name}.`);
    } else {
      setLiveBadge('POR DEBAJO DEL RANGO ESPERADO', 'badge-danger', `Baja densidad ósea para la edad (Z-Score ≤ -2.0) en ${minScore.name}.`);
    }
  }
}

function setLiveBadge(text, className, desc) {
  const liveBadge = document.getElementById('live-dxa-badge');
  const liveDesc = document.getElementById('live-dxa-desc');
  if (liveBadge) {
    liveBadge.className = `badge ${className}`;
    liveBadge.textContent = text;
  }
  if (liveDesc) liveDesc.textContent = desc;
}
