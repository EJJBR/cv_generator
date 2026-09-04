const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const docenteSearch = document.getElementById('docente-search');
const docenteRowsContainer = document.getElementById('docente-rows');
const excelInput = document.getElementById('excel-input');
const excelFileName = document.getElementById('excel-file-name');
const processExcel = document.getElementById('process-excel');

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.panel).classList.add('active');
  });
});

docenteSearch?.addEventListener('input', (event) => {
  const query = event.target.value.trim().toLocaleLowerCase();

  docenteRowsContainer?.querySelectorAll('tr').forEach((row) => {
    row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
  });
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
      processExcel.dataset.stage = 'done';
      processExcel.innerHTML = 'CVs listos <b>✓</b>';
      alert('La descarga terminó.');
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

function updateDownloadLog(filas) {
  const logNode = document.getElementById('download-log');
  if (!logNode) return;

  const resumen = filas.filter((fila) => Boolean(fila.descargada)).length;
  const errores = filas.filter((fila) => Boolean(fila.fallida)).length;
  const pendientes = filas.filter((fila) => !fila.descargada && !fila.fallida && fila.tiene_enlace).length;

  logNode.innerHTML = `
    <strong>Estado:</strong>
    <span class="status-ok">${resumen} descargadas</span>
    <span class="status-warn">${pendientes} pendientes</span>
    <span class="status-error">${errores} con error</span>
  `;
}

function renderDocentes(filas, mensaje = '') {
  if (!docenteRowsContainer) return;

  docenteRowsContainer.innerHTML = filas.map((fila) => {
    const tieneEnlace = Boolean(fila.tiene_enlace);
    const descargada = Boolean(fila.descargada);
    const fallida = Boolean(fila.fallida);
    const retryButton = fallida ? '<button class="retry-action" type="button" data-id="' + (fila.id || '') + '">Reintentar</button>' : '';
    const estado = fila.estado || (tieneEnlace ? 'Pendiente de descarga' : 'Sin enlace');
    const estadoClass = descargada ? 'status-ok' : fallida ? 'status-error' : 'status-warn';

    return `
      <tr class="${tieneEnlace ? '' : 'no-photo'} ${fallida ? 'failed-row' : ''}">
        <td>${fila.id || ''}</td>
        <td><strong>${fila.nombre || 'Sin nombre'}</strong></td>
        <td>
          <div class="download-state ${fallida ? 'failed' : ''}">
            <small class="${estadoClass}">${estado}</small>
            ${retryButton}
          </div>
        </td>
        <td><button class="table-action" type="button" ${!descargada ? 'disabled' : ''}>Ver CV</button></td>
      </tr>`;
  }).join('');

  updateDownloadLog(filas);

  document.getElementById('total-docentes').textContent = filas.length;
  document.getElementById('total-enlaces').textContent = filas.filter((fila) => Boolean(fila.tiene_enlace)).length;
  document.getElementById('total-pendientes').textContent = filas.filter((fila) => !fila.tiene_enlace || fila.fallida).length;

  if (mensaje) {
    const logNode = document.getElementById('download-log');
    if (logNode) {
      logNode.innerHTML = `<strong>Estado:</strong> ${mensaje.replace(/\n/g, '<br>')}`;
    }
  }

  docenteRowsContainer.querySelectorAll('.retry-action').forEach((button) => {
    button.addEventListener('click', async () => {
      const file = excelInput?.files?.[0];
      if (!file) {
        alert('Selecciona un archivo Excel primero.');
        return;
      }

      const formData = new FormData();
      formData.append('excel', file);
      button.disabled = true;
      button.textContent = 'Reintentando...';

      try {
        const response = await fetch('/masivo/descargar', {method: 'POST', body: formData});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'No se pudo reintentar la descarga.');
        renderDocentes(result.filas, result.mensaje || '');
      } catch (error) {
        alert(error.message);
      }
    });
  });
}
