const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const docenteSearch = document.getElementById('docente-search');
const docenteRowsContainer = document.getElementById('docente-rows');
const excelInput = document.getElementById('excel-input');
const excelFileName = document.getElementById('excel-file-name');
const processExcel = document.getElementById('process-excel');
const pagination = document.getElementById('docente-pagination');
const paginationSummary = document.getElementById('pagination-summary');
const paginationPage = document.getElementById('pagination-page');
const paginationPrev = document.getElementById('pagination-prev');
const paginationNext = document.getElementById('pagination-next');
const pageSizeInput = document.getElementById('page-size');
let todasLasFilas = [];
let paginaActual = 1;

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
  });
});

docenteSearch?.addEventListener('input', () => {
  paginaActual = 1;
  renderPagina();
});

paginationPrev?.addEventListener('click', () => {
  if (paginaActual > 1) {
    paginaActual -= 1;
    renderPagina();
  }
});

paginationNext?.addEventListener('click', () => {
  const totalPaginas = Math.ceil(filasVisibles().length / Number(pageSizeInput.value));
  if (paginaActual < totalPaginas) {
    paginaActual += 1;
    renderPagina();
  }
});

pageSizeInput?.addEventListener('change', () => {
  paginaActual = 1;
  renderPagina();
});

excelInput?.addEventListener('change', () => {
  const file = excelInput.files?.[0];
  if (file && excelFileName) excelFileName.textContent = file.name;
});

processExcel?.addEventListener('click', async () => {
  const file = excelInput?.files?.[0];
  if (!file) {
    alert('Selecciona un archivo Excel primero.');
    return;
  }

  const stage = processExcel.dataset.stage || 'process';
  const isProcessing = processExcel.dataset.loading === 'true';
  if (isProcessing) return;

  const formData = new FormData();
  formData.append('excel', file);
  processExcel.disabled = true;
  processExcel.dataset.loading = 'true';
  processExcel.innerHTML = stage === 'process' ? 'Procesando... <b>→</b>' : 'Descargando... <b>→</b>';

  try {
    const endpoint = stage === 'process' ? '/masivo/procesar' : '/masivo/descargar';
    const response = await fetch(endpoint, {method: 'POST', body: formData});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo completar la operación.');

    renderDocentes(result.filas, result.mensaje || '');

    if (stage === 'process') {
      processExcel.dataset.stage = 'download';
      processExcel.innerHTML = 'Descargar imágenes <b>→</b>';
    } else {
      processExcel.dataset.stage = 'download';
      processExcel.innerHTML = 'Descargando... <b>↻</b>';
      await monitorDownload(result.task_id);
    }
  } catch (error) {
    processExcel.dataset.stage = 'process';
    processExcel.innerHTML = 'Procesar Excel <b>→</b>';
    alert(error.message);
  } finally {
    processExcel.disabled = false;
    processExcel.dataset.loading = 'false';
  }
});

function combinarFilasReintento(filasNuevas, idsActualizados) {
  if (!idsActualizados) return filasNuevas;

  const ids = new Set(idsActualizados);
  const filasActuales = new Map(todasLasFilas.map((fila) => [String(fila.id), fila]));
  return filasNuevas.map((fila) => (
    ids.has(String(fila.id)) ? fila : (filasActuales.get(String(fila.id)) || fila)
  ));
}

async function monitorDownload(taskId, idsActualizados = null) {
  let estado = 'running';
  while (estado === 'running') {
    await new Promise((resolve) => setTimeout(resolve, 700));
    const response = await fetch(`/masivo/descargar/${taskId}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo consultar la descarga.');
    estado = result.estado;
    renderDocentes(
      combinarFilasReintento(result.filas, idsActualizados),
      result.mensaje || '',
    );
  }

  processExcel.dataset.stage = 'done';
  processExcel.innerHTML = 'Descarga terminada <b>✓</b>';
  processExcel.disabled = false;
  alert(estado === 'completed' ? 'La descarga terminó.' : 'La descarga terminó con errores.');
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[character]));
}

function updateDownloadLog(filas) {
  const logNode = document.getElementById('download-log');
  if (!logNode) return;

  const resumen = filas.filter((fila) => Boolean(fila.descargada)).length;
  const filasConError = filas.filter((fila) => Boolean(fila.fallida));
  const filasSinEnlace = filas.filter((fila) => !fila.tiene_enlace);
  const errores = filasConError.length;
  const pendientes = filas.filter((fila) => !fila.descargada && !fila.fallida && fila.tiene_enlace).length;
  const detalleErrores = filasConError.length
    ? `<div class="download-errors"><strong>Reintentar:</strong>${filasConError.map((fila) => `
        <span class="download-error-item">ID ${escapeHtml(fila.id || 'sin ID')} - ${escapeHtml(fila.nombre || 'Sin nombre')}</span>`).join('')}</div>`
    : '';
  const detalleSinEnlace = filasSinEnlace.length
    ? `<div class="download-missing"><strong>Sin enlace:</strong>${filasSinEnlace.map((fila) => `
        <span class="download-missing-item">ID ${escapeHtml(fila.id || 'sin ID')} - ${escapeHtml(fila.nombre || 'Sin nombre')}</span>`).join('')}</div>`
    : '';

  logNode.innerHTML = `
    <strong>Estado:</strong>
    <span class="status-ok">${resumen} descargadas</span>
    <span class="status-warn">${filasSinEnlace.length} sin enlace</span>
    <span class="status-warn">${pendientes} pendientes</span>
    <span class="status-error">${errores} con error</span>
    ${detalleSinEnlace}
    ${detalleErrores}
  `;
}

function updateDownloadProgress(filas) {
  const progressBar = document.getElementById('download-progress-bar');
  const progressTrack = progressBar?.parentElement;
  const progressCount = document.getElementById('download-progress-count');
  const progressLabel = document.getElementById('download-progress-label');
  if (!progressBar || !progressTrack || !progressCount || !progressLabel) return;

  const conEnlace = filas.filter((fila) => Boolean(fila.tiene_enlace));
  const terminadas = conEnlace.filter((fila) => Boolean(fila.descargada || fila.fallida)).length;
  const descargadas = conEnlace.filter((fila) => Boolean(fila.descargada)).length;
  const porcentaje = conEnlace.length ? Math.round((terminadas / conEnlace.length) * 100) : 0;

  progressBar.style.width = `${porcentaje}%`;
  progressTrack.setAttribute('aria-valuenow', String(porcentaje));
  progressCount.textContent = `${terminadas} de ${conEnlace.length}`;
  progressLabel.textContent = porcentaje === 100 && conEnlace.length
    ? `Descarga terminada: ${descargadas} correctas`
    : `Progreso de descarga: ${porcentaje}%`;
}

function filasVisibles() {
  const query = docenteSearch?.value.trim().toLocaleLowerCase() || '';
  return todasLasFilas.filter((fila) => {
    if (!query) return true;
    return `${fila.id || ''} ${fila.nombre || ''} ${fila.estado || ''}`
      .toLocaleLowerCase()
      .includes(query);
  });
}

function renderFila(fila) {
    const tieneEnlace = Boolean(fila.tiene_enlace);
    const descargada = Boolean(fila.descargada);
    const fallida = Boolean(fila.fallida);
    const retryButton = fallida ? '<button class="retry-action" type="button" data-id="' + (fila.id || '') + '">Reintentar</button>' : '';
    const imageButton = descargada
      ? '<button class="view-image" type="button" data-id="' + (fila.id || '') + '" title="Abrir imagen">Ver imagen</button>'
      : '';
    const estado = fila.estado || (tieneEnlace ? 'Pendiente de descarga' : 'Sin enlace');
    const estadoClass = descargada ? 'status-ok' : fallida ? 'status-error' : 'status-warn';
    const filaClass = descargada ? 'downloaded-row' : fallida ? 'failed-row' : tieneEnlace ? 'downloading-row' : 'no-photo';

    return `
      <tr class="${filaClass}">
        <td>${fila.id || ''}</td>
        <td><strong>${fila.nombre || 'Sin nombre'}</strong></td>
        <td>
          <div class="download-state ${fallida ? 'failed' : ''}">
            <small class="${estadoClass}">${estado}</small>
            ${imageButton}
            ${retryButton}
          </div>
        </td>
        <td><button class="table-action" type="button" ${!descargada ? 'disabled' : ''}>Ver CV</button></td>
      </tr>`;
}

function attachRetryHandlers() {
  docenteRowsContainer.querySelectorAll('.view-image').forEach((button) => {
    button.addEventListener('click', () => {
      window.open(`/masivo/imagen/${encodeURIComponent(button.dataset.id || '')}`, '_blank', 'noopener');
    });
  });

  docenteRowsContainer.querySelectorAll('.retry-action').forEach((button) => {
    button.addEventListener('click', async () => {
      const file = excelInput?.files?.[0];
      if (!file) {
        alert('Selecciona un archivo Excel primero.');
        return;
      }

      const formData = new FormData();
      formData.append('excel', file);
      const idReintento = button.dataset.id || '';
      formData.append('id_reintento', idReintento);
      button.disabled = true;
      button.textContent = 'Reintentando...';

      try {
        const response = await fetch('/masivo/descargar', {method: 'POST', body: formData});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'No se pudo reintentar la descarga.');
        const idsActualizados = new Set([idReintento]);
        renderDocentes(
          combinarFilasReintento(result.filas, idsActualizados),
          'Reintento iniciado.',
        );
        await monitorDownload(result.task_id, idsActualizados);
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

function renderPagina() {
  if (!docenteRowsContainer) return;

  const visibles = filasVisibles();
  const pageSize = Number(pageSizeInput?.value || 20);
  const totalPaginas = Math.max(1, Math.ceil(visibles.length / pageSize));
  paginaActual = Math.min(paginaActual, totalPaginas);
  const inicio = (paginaActual - 1) * pageSize;
  const pagina = visibles.slice(inicio, inicio + pageSize);

  docenteRowsContainer.innerHTML = pagina.length
    ? pagina.map(renderFila).join('')
    : '<tr><td colspan="4" class="empty-table">No se encontraron docentes.</td></tr>';

  if (pagination) pagination.hidden = todasLasFilas.length === 0;
  if (paginationSummary) {
    paginationSummary.textContent = visibles.length
      ? `Mostrando ${inicio + 1}-${Math.min(inicio + pageSize, visibles.length)} de ${visibles.length}`
      : 'Sin resultados';
  }
  if (paginationPage) paginationPage.textContent = `Página ${paginaActual} de ${totalPaginas}`;
  if (paginationPrev) paginationPrev.disabled = paginaActual <= 1;
  if (paginationNext) paginationNext.disabled = paginaActual >= totalPaginas;
  attachRetryHandlers();
}

function renderDocentes(filas, mensaje = '') {
  if (!docenteRowsContainer) return;

  todasLasFilas = filas;
  renderPagina();

  updateDownloadLog(filas);
  updateDownloadProgress(filas);

  document.getElementById('total-docentes').textContent = filas.length;
  document.getElementById('total-enlaces').textContent = filas.filter((fila) => Boolean(fila.tiene_enlace)).length;
  document.getElementById('total-pendientes').textContent = filas.filter((fila) => !fila.tiene_enlace || fila.fallida).length;

}
