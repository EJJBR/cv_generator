const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const docenteSearch = document.getElementById('docente-search');
const statusFilter = document.getElementById('status-filter');
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
const imageModal = document.getElementById('image-modal');
const imageModalImage = document.getElementById('image-modal-image');
const imageModalTitle = document.getElementById('image-modal-title');
const imageModalClose = document.getElementById('image-modal-close');
const imageModalPdf = document.getElementById('image-modal-pdf');
const previewPrev = document.getElementById('preview-prev');
const previewNext = document.getElementById('preview-next');
const chooseOutputFolder = document.getElementById('choose-output-folder');
const saveCvs = document.getElementById('save-cvs');
const clearMassiveOutput = document.getElementById('clear-massive-output');
let todasLasFilas = [];
let paginaActual = 1;
let vistaPreviaActual = null;
let outputFolderHandle = null;

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

statusFilter?.addEventListener('change', () => {
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

chooseOutputFolder?.addEventListener('click', async () => {
  if (!window.showDirectoryPicker) {
    alert('Tu navegador no permite seleccionar carpetas. Usa Chrome o Edge actualizado.');
    return;
  }
  try {
    outputFolderHandle = await window.showDirectoryPicker({mode: 'readwrite'});
    chooseOutputFolder.textContent = `Carpeta: ${outputFolderHandle.name}`;
  } catch (error) {
    if (error.name !== 'AbortError') alert('No se pudo seleccionar la carpeta.');
  }
});

function nombrePdfDesdeFila(fila) {
  const nombre = String(fila.nombre || '')
    .toLocaleUpperCase()
    .split('')
    .filter((character) => /[\p{L}\p{N} _-]/u.test(character))
    .join('')
    .trim()
    .replace(/ /g, '_');
  return `${fila.id}_CV_${nombre || 'SIN_NOMBRE'}.pdf`;
}

saveCvs?.addEventListener('click', async () => {
  const filas = todasLasFilas.filter((fila) => fila.cv_generado);
  if (!filas.length) {
    alert('Todavía no hay CVs generados para guardar.');
    return;
  }
  if (!outputFolderHandle) {
    alert('Primero selecciona una carpeta de destino.');
    return;
  }
  saveCvs.disabled = true;
  saveCvs.textContent = 'Guardando...';
  try {
    for (const fila of filas) {
      const response = await fetch(`/masivo/cv/${encodeURIComponent(fila.id)}`);
      if (!response.ok) continue;
      const nombre = nombrePdfDesdeFila(fila);
      const archivo = await outputFolderHandle.getFileHandle(nombre, {create: true});
      const writable = await archivo.createWritable();
      await writable.write(await response.blob());
      await writable.close();
    }
    alert(`Se guardaron ${filas.length} CVs en la carpeta seleccionada.`);
  } catch (error) {
    alert(`No se pudieron guardar los CVs: ${error.message}`);
  } finally {
    saveCvs.disabled = false;
    saveCvs.innerHTML = 'Guardar CVs <b>↓</b>';
  }
});

clearMassiveOutput?.addEventListener('click', async () => {
  if (!confirm('Se eliminarán las imágenes, los CVs y los Excels limpios generados. ¿Continuar?')) return;
  try {
    const response = await fetch('/masivo/limpiar', {method: 'POST'});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo limpiar la salida.');
    todasLasFilas = [];
    paginaActual = 1;
    renderDocentes([]);
    processExcel.dataset.stage = 'process';
    processExcel.innerHTML = 'Procesar Excel <b>→</b>';
    chooseOutputFolder.textContent = 'Elegir carpeta de destino';
    outputFolderHandle = null;
    alert(result.mensaje);
  } catch (error) {
    alert(error.message);
  }
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
  processExcel.innerHTML = stage === 'process'
    ? 'Procesando... <b>→</b>'
    : stage === 'download' ? 'Descargando... <b>→</b>' : 'Generando CVs... <b>→</b>';

  try {
    const endpoint = stage === 'process'
      ? '/masivo/procesar'
      : stage === 'download' ? '/masivo/descargar' : '/masivo/generar';
    const response = await fetch(endpoint, {method: 'POST', body: formData});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo completar la operación.');

    renderDocentes(result.filas, result.mensaje || '');
    if (stage === 'generate') {
      updateGenerationProgress(result.cv_completados || 0, result.cv_total || result.filas.length);
    }

    if (stage === 'process') {
      processExcel.dataset.stage = 'download';
      processExcel.innerHTML = 'Descargar imágenes <b>→</b>';
    } else if (stage === 'download') {
      processExcel.dataset.stage = 'generate';
      processExcel.innerHTML = 'Descargando... <b>↻</b>';
      await monitorDownload(result.task_id);
    } else {
      processExcel.dataset.stage = 'generate';
      processExcel.innerHTML = 'Generando CVs... <b>↻</b>';
      await monitorGeneration(result.task_id);
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

  processExcel.dataset.stage = estado === 'completed' || estado === 'failed' ? 'generate' : 'done';
  processExcel.innerHTML = 'Generar CVs <b>→</b>';
  processExcel.disabled = false;
  alert(estado === 'completed' ? 'La descarga terminó.' : 'La descarga terminó con errores.');
}

async function monitorGeneration(taskId) {
  let estado = 'running';
  while (estado === 'running') {
    await new Promise((resolve) => setTimeout(resolve, 700));
    const response = await fetch(`/masivo/generar/${taskId}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo consultar la generación de CVs.');
    estado = result.estado;
    renderDocentes(result.filas, result.mensaje || '');
    updateGenerationProgress(result.cv_completados, result.cv_total);
  }

  processExcel.dataset.stage = 'done';
  processExcel.innerHTML = 'CVs generados <b>✓</b>';
  processExcel.disabled = false;
  alert(estado === 'completed' ? 'La generación de CVs terminó.' : 'La generación de CVs terminó con errores.');
}

function updateGenerationProgress(completados, total) {
  const progressBar = document.getElementById('download-progress-bar');
  const progressTrack = progressBar?.parentElement;
  const progressCount = document.getElementById('download-progress-count');
  const progressLabel = document.getElementById('download-progress-label');
  if (!progressBar || !progressTrack || !progressCount || !progressLabel) return;

  const porcentaje = total ? Math.round((completados / total) * 100) : 0;
  progressBar.style.width = `${porcentaje}%`;
  progressTrack.setAttribute('aria-valuenow', String(porcentaje));
  progressCount.textContent = `${completados} de ${total}`;
  progressLabel.textContent = porcentaje === 100 && total
    ? 'Generación terminada'
    : `Generación de CVs: ${porcentaje}%`;
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
    ? `<div class="download-missing"><strong>Sin enlace:</strong><span class="download-missing-item">${filasSinEnlace.map((fila) => escapeHtml(fila.id || 'sin ID')).join(', ')}</span></div>`
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
  const filtro = statusFilter?.value || 'all';
  return todasLasFilas.filter((fila) => {
    const coincideFiltro = filtro === 'all'
      || (filtro === 'missing-link' && !fila.tiene_enlace)
      || (filtro === 'failed' && fila.fallida);
    if (!coincideFiltro) return false;
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
    const localImageButton = !tieneEnlace && !descargada
      ? '<button class="local-image-action" type="button" data-id="' + (fila.id || '') + '" data-nombre="' + escapeHtml(fila.nombre || '') + '">Elegir imagen</button>'
      : '';
    const imageButton = descargada
      ? '<button class="view-image" type="button" data-id="' + (fila.id || '') + '" data-nombre="' + escapeHtml(fila.nombre || '') + '" title="Abrir imagen">Ver imagen</button>'
      : '';
    const cvButton = fila.cv_generado
      ? '<button class="table-action view-cv" type="button" data-id="' + (fila.id || '') + '" title="Abrir CV">Ver CV</button>'
      : descargada
        ? '<button class="generate-cv-action" type="button" data-id="' + (fila.id || '') + '">Generar CV</button>'
      : '';
    const cvError = fila.cv_error
      ? `<span class="cv-error" title="${escapeHtml(fila.cv_mensaje || '')}">No se pudo generar</span>`
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
            ${localImageButton}
            ${retryButton}
          </div>
        </td>
        <td>${cvButton}${cvError}</td>
      </tr>`;
}

function cerrarVistaPrevia() {
  if (!imageModal) return;
  imageModal.hidden = true;
  document.body.classList.remove('modal-open');
  if (imageModalImage) imageModalImage.src = '';
  if (imageModalPdf) imageModalPdf.src = '';
  vistaPreviaActual = null;
}

function recursoDisponible(fila, tipo) {
  return tipo === 'image' ? Boolean(fila.descargada) : Boolean(fila.cv_generado);
}

function renderVistaPrevia() {
  if (!vistaPreviaActual || !imageModal) return;
  const {fila, tipo} = vistaPreviaActual;
  imageModalTitle.textContent = `${tipo === 'image' ? 'Imagen' : 'CV'} · ${fila.id} - ${fila.nombre || 'Sin nombre'}`;
  imageModalImage.hidden = tipo !== 'image';
  imageModalPdf.hidden = tipo !== 'cv';
  imageModalImage.src = tipo === 'image' ? `/masivo/imagen/${encodeURIComponent(fila.id)}` : '';
  imageModalPdf.src = tipo === 'cv' ? `/masivo/cv/${encodeURIComponent(fila.id)}` : '';
  const indice = todasLasFilas.findIndex((item) => String(item.id) === String(fila.id));
  const tieneAnterior = todasLasFilas.slice(0, indice).some((item) => recursoDisponible(item, tipo));
  const tieneSiguiente = todasLasFilas.slice(indice + 1).some((item) => recursoDisponible(item, tipo));
  previewPrev.disabled = !tieneAnterior;
  previewNext.disabled = !tieneSiguiente;
}

function abrirVistaPrevia(id, tipo) {
  const fila = todasLasFilas.find((item) => String(item.id) === String(id));
  if (!imageModal || !fila || !recursoDisponible(fila, tipo)) return;
  vistaPreviaActual = {fila, tipo};
  renderVistaPrevia();
  imageModal.hidden = false;
  document.body.classList.add('modal-open');
  imageModalClose?.focus();
}

function desplazarVistaPrevia(direccion) {
  if (!vistaPreviaActual) return;
  const indice = todasLasFilas.findIndex((item) => String(item.id) === String(vistaPreviaActual.fila.id));
  const paso = direccion > 0 ? 1 : -1;
  let siguiente = indice + paso;
  while (siguiente >= 0 && siguiente < todasLasFilas.length) {
    if (recursoDisponible(todasLasFilas[siguiente], vistaPreviaActual.tipo)) {
      vistaPreviaActual.fila = todasLasFilas[siguiente];
      renderVistaPrevia();
      return;
    }
    siguiente += paso;
  }
}

function cambiarTipoVistaPrevia(tipo) {
  if (vistaPreviaActual && recursoDisponible(vistaPreviaActual.fila, tipo)) {
    vistaPreviaActual.tipo = tipo;
    renderVistaPrevia();
  }
}

imageModalClose?.addEventListener('click', cerrarVistaPrevia);
imageModal?.addEventListener('click', (event) => {
  if (event.target === imageModal) cerrarVistaPrevia();
});
previewPrev?.addEventListener('click', () => desplazarVistaPrevia(-1));
previewNext?.addEventListener('click', () => desplazarVistaPrevia(1));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && imageModal && !imageModal.hidden) cerrarVistaPrevia();
  if (!imageModal || imageModal.hidden || !vistaPreviaActual) return;
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    desplazarVistaPrevia(-1);
  } else if (event.key === 'ArrowDown') {
    event.preventDefault();
    desplazarVistaPrevia(1);
  } else if (event.key === 'ArrowRight') {
    event.preventDefault();
    cambiarTipoVistaPrevia('cv');
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault();
    cambiarTipoVistaPrevia('image');
  }
});

function attachRetryHandlers() {
  docenteRowsContainer.querySelectorAll('.local-image-action').forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.addEventListener('change', async () => {
        const imagen = input.files?.[0];
        if (!imagen) return;
        const formData = new FormData();
        formData.append('imagen', imagen);
        formData.append('id_val', button.dataset.id || '');
        formData.append('nombre', button.dataset.nombre || '');
        button.disabled = true;
        button.textContent = 'Guardando...';
        try {
          const response = await fetch('/masivo/imagen-local', {method: 'POST', body: formData});
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'No se pudo guardar la imagen.');
          const fila = todasLasFilas.find((item) => String(item.id) === String(result.id));
          if (fila) Object.assign(fila, result);
          renderPagina();
          updateDownloadLog(todasLasFilas);
          updateDownloadProgress(todasLasFilas);
        } catch (error) {
          button.disabled = false;
          button.textContent = 'Elegir imagen';
          alert(error.message);
        }
      });
      input.click();
    });
  });

  docenteRowsContainer.querySelectorAll('.generate-cv-action').forEach((button) => {
    button.addEventListener('click', async () => {
      const file = excelInput?.files?.[0];
      if (!file) {
        alert('Selecciona un archivo Excel primero.');
        return;
      }
      const formData = new FormData();
      formData.append('excel', file);
      formData.append('id_val', button.dataset.id || '');
      button.disabled = true;
      button.textContent = 'Generando...';
      try {
        const response = await fetch('/masivo/generar-cv', {method: 'POST', body: formData});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'No se pudo generar el CV.');
        const fila = todasLasFilas.find((item) => String(item.id) === String(result.id));
        if (fila) Object.assign(fila, result);
        renderPagina();
      } catch (error) {
        button.disabled = false;
        button.textContent = 'Generar CV';
        alert(error.message);
      }
    });
  });

  docenteRowsContainer.querySelectorAll('.view-cv').forEach((button) => {
    button.addEventListener('click', () => {
      abrirVistaPrevia(button.dataset.id || '', 'cv');
    });
  });

  docenteRowsContainer.querySelectorAll('.view-image').forEach((button) => {
    button.addEventListener('click', () => {
      abrirVistaPrevia(button.dataset.id || '', 'image');
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
