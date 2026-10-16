/**
 * Utilidades Globales de Web-CalcMed (common.js)
 * Manejo de temas (Dark/Light), portapapeles, modales y búsqueda de pacientes.
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initModals();
  initPatientAutocomplete();
});

/* 1. Gestión de Tema Claro / Oscuro */
function initTheme() {
  const savedTheme = localStorage.getItem('calcmed_theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  } else {
    document.body.classList.remove('light-theme');
  }

  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      const current = document.body.classList.contains('light-theme') ? 'light' : 'dark';
      localStorage.setItem('calcmed_theme', current);
      updateThemeIcon(toggleBtn, current);
    });
    updateThemeIcon(toggleBtn, savedTheme);
  }
}

function updateThemeIcon(btn, theme) {
  btn.innerHTML = theme === 'light' ? '🌙 Modo Oscuro' : '☀️ Modo Claro';
}

/* 2. Copiado al Portapapeles con Notificación Toast */
window.copyReportToClipboard = function (elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const textToCopy = el.innerText || el.textContent;
  navigator.clipboard.writeText(textToCopy).then(() => {
    showToast('✓ Informe copiado al portapapeles para RIS/PACS', 'success');
  }).catch(() => {
    // Fallback para navegadores antiguos
    const textarea = document.createElement('textarea');
    textarea.value = textToCopy;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('✓ Informe copiado al portapapeles', 'success');
  });
};

function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container no-print';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* 3. Gestión de Modales */
function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) modal.classList.add('active');
    });
  });

  document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el) {
        el.closest('.modal-overlay').classList.remove('active');
      }
    });
  });
}

/* 4. Autocompletado Seguro de Pacientes */
function initPatientAutocomplete() {
  const cedulaInput = document.getElementById('cedula_id');
  if (!cedulaInput) return;

  let debounceTimer;
  cedulaInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = cedulaInput.value.trim();
    if (query.length < 3) return;

    debounceTimer = setTimeout(() => {
      fetch(`/api/pacientes/search?q=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(results => {
          if (results && results.length > 0) {
            const first = results[0];
            const nombreInput = document.getElementById('nombre');
            const edadInput = document.getElementById('edad');
            const sexoSelect = document.getElementById('sexo');
            const medInput = document.getElementById('medico_solicitante');

            if (nombreInput && !nombreInput.value) nombreInput.value = first.nombre || '';
            if (edadInput && (!edadInput.value || edadInput.value === '50')) edadInput.value = first.edad || '';
            if (sexoSelect) sexoSelect.value = first.sexo || 'F';
            if (medInput && !medInput.value) medInput.value = first.medico_solicitante || '';
          }
        })
        .catch(() => {});
    }, 400);
  });
}
