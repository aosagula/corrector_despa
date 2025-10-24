// Main Application Logic

// Toast Notification Function
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = `toast-${Date.now()}`;

    const bgClass = type === 'success' ? 'bg-success' :
                    type === 'error' ? 'bg-danger' :
                    type === 'warning' ? 'bg-warning' : 'bg-info';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });

    toast.show();

    // Remover del DOM después de ocultarse
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Confirm Delete Modal Function
function showConfirmDelete(message, onConfirm) {
    const modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
    const messageElement = document.getElementById('confirmDeleteMessage');
    const confirmBtn = document.getElementById('confirmDeleteBtn');

    // Actualizar mensaje
    messageElement.textContent = message;

    // Remover listeners anteriores clonando el botón
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    // Agregar nuevo listener
    newConfirmBtn.addEventListener('click', function() {
        modal.hide();
        onConfirm();
    });

    modal.show();
}

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize event listeners
    setupCommercialUpload();
    setupProvisionalUpload();
    setupComparison();
    setupAttributes();
    setupTabNavigation();

    // Load initial data
    loadCommercialDocuments();
    loadProvisionalDocuments();
    loadAttributes();
    loadHistory();
}

// Tab Navigation
function setupTabNavigation() {
    const tabs = document.querySelectorAll('#mainTabs .nav-link');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('href');

            if (target === '#compare') {
                populateComparisonSelects();
            } else if (target === '#history') {
                loadHistory();
            }
        });
    });
}

// Commercial Documents Upload
function setupCommercialUpload() {
    const form = document.getElementById('commercialUploadForm');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const fileInput = document.getElementById('commercialFile');
        const file = fileInput.files[0];

        if (!file) {
            showAlert('commercialUploadResult', 'Por favor selecciona un archivo', 'warning');
            return;
        }

        showProgress('commercialUploadProgress', true);
        hideAlert('commercialUploadResult');

        try {
            const result = await DocumentAPI.uploadCommercialDocument(file);

            showProgress('commercialUploadProgress', false);
            showAlert('commercialUploadResult',
                `Documento subido exitosamente!<br>
                Tipo: ${result.document_type}<br>
                Confianza: ${(result.classification_confidence * 100).toFixed(1)}%`,
                'success'
            );

            form.reset();
            loadCommercialDocuments();
        } catch (error) {
            showProgress('commercialUploadProgress', false);
            showAlert('commercialUploadResult', `Error: ${error.message}`, 'danger');
        }
    });
}

// Provisional Documents Upload
function setupProvisionalUpload() {
    const form = document.getElementById('provisionalUploadForm');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const fileInput = document.getElementById('provisionalFile');
        const file = fileInput.files[0];

        if (!file) {
            showAlert('provisionalUploadResult', 'Por favor selecciona un archivo', 'warning');
            return;
        }

        showProgress('provisionalUploadProgress', true);
        hideAlert('provisionalUploadResult');

        try {
            const result = await DocumentAPI.uploadProvisionalDocument(file);

            showProgress('provisionalUploadProgress', false);
            showAlert('provisionalUploadResult',
                `Documento provisorio subido exitosamente!`,
                'success'
            );

            form.reset();
            loadProvisionalDocuments();
        } catch (error) {
            showProgress('provisionalUploadProgress', false);
            showAlert('provisionalUploadResult', `Error: ${error.message}`, 'danger');
        }
    });
}

// Load Commercial Documents
async function loadCommercialDocuments() {
    const container = document.getElementById('commercialDocumentsList');

    try {
        const documents = await DocumentAPI.listCommercialDocuments();

        if (documents.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay documentos comerciales subidos.</p>';
            return;
        }

        container.innerHTML = documents.map(doc => createDocumentCard(doc, 'commercial')).join('');
    } catch (error) {
        container.innerHTML = `<p class="text-danger">Error cargando documentos: ${error.message}</p>`;
    }
}

// Load Provisional Documents
async function loadProvisionalDocuments() {
    const container = document.getElementById('provisionalDocumentsList');

    try {
        const documents = await DocumentAPI.listProvisionalDocuments();

        if (documents.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay documentos provisorios subidos.</p>';
            return;
        }

        container.innerHTML = documents.map(doc => createDocumentCard(doc, 'provisional')).join('');
    } catch (error) {
        container.innerHTML = `<p class="text-danger">Error cargando documentos: ${error.message}</p>`;
    }
}

// Create Document Card HTML
function createDocumentCard(doc, type) {
    const typeClass = doc.document_type ? `badge-${doc.document_type}` : 'badge-desconocido';
    const typeBadge = doc.document_type
        ? `<span class="document-type-badge ${typeClass}">${doc.document_type.replace('_', ' ')}</span>`
        : '';

    const confidenceBadge = doc.classification_confidence
        ? `<small class="text-muted">Confianza: ${(doc.classification_confidence * 100).toFixed(1)}%</small>`
        : '';

    return `
        <div class="document-item">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6 class="mb-2">
                        <i class="bi bi-file-earmark-text"></i> ${doc.filename}
                    </h6>
                    ${typeBadge} ${confidenceBadge}
                    <div class="mt-2">
                        <small class="text-muted">ID: ${doc.id} | Fecha: ${new Date(doc.created_at).toLocaleString()}</small>
                    </div>
                </div>
                <div class="btn-group-sm">
                    <button class="btn btn-sm btn-info" onclick="viewDocumentData(${doc.id}, '${type}')">
                        <i class="bi bi-eye"></i> Ver Datos
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="viewDocumentContent(${doc.id}, '${type}')">
                        <i class="bi bi-file-text"></i> Ver Contenido
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteDocument(${doc.id}, '${type}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div id="docData-${type}-${doc.id}" class="extracted-data" style="display: none;">
                <pre>${JSON.stringify(doc.extracted_data, null, 2)}</pre>
            </div>
        </div>
    `;
}

// View Document Data
function viewDocumentData(id, type) {
    const dataDiv = document.getElementById(`docData-${type}-${id}`);
    if (dataDiv.style.display === 'none') {
        dataDiv.style.display = 'block';
    } else {
        dataDiv.style.display = 'none';
    }
}

// Delete Document
async function deleteDocument(id, type) {
    const docType = type === 'commercial' ? 'comercial' : 'provisorio';

    showConfirmDelete(
        `¿Estás seguro de que deseas eliminar este documento ${docType}?`,
        async function() {
            try {
                if (type === 'commercial') {
                    await DocumentAPI.deleteCommercialDocument(id);
                    loadCommercialDocuments();
                } else {
                    await DocumentAPI.deleteProvisionalDocument(id);
                    loadProvisionalDocuments();
                }

                showToast('Documento eliminado exitosamente', 'success');
            } catch (error) {
                showToast(`Error eliminando documento: ${error.message}`, 'error');
            }
        }
    );
}

// Comparison Setup
function setupComparison() {
    const form = document.getElementById('compareForm');
    const batchBtn = document.getElementById('batchCompareBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const commercialId = document.getElementById('selectCommercial').value;
        const provisionalId = document.getElementById('selectProvisional').value;

        if (!commercialId || !provisionalId) {
            alert('Por favor selecciona ambos documentos');
            return;
        }

        showProgress('compareProgress', true);

        try {
            const result = await DocumentAPI.createComparison(
                parseInt(commercialId),
                parseInt(provisionalId)
            );

            showProgress('compareProgress', false);
            displayComparisonResult(result);
        } catch (error) {
            showProgress('compareProgress', false);
            alert(`Error en comparación: ${error.message}`);
        }
    });

    batchBtn.addEventListener('click', async function() {
        const provisionalId = document.getElementById('selectProvisional').value;

        if (!provisionalId) {
            alert('Por favor selecciona un documento provisorio');
            return;
        }

        showProgress('compareProgress', true);

        try {
            const result = await DocumentAPI.batchCompare(parseInt(provisionalId));

            showProgress('compareProgress', false);
            displayBatchComparisonResults(result);
        } catch (error) {
            showProgress('compareProgress', false);
            alert(`Error en comparación por lotes: ${error.message}`);
        }
    });
}

// Populate Comparison Selects
async function populateComparisonSelects() {
    try {
        const [commercial, provisional] = await Promise.all([
            DocumentAPI.listCommercialDocuments(),
            DocumentAPI.listProvisionalDocuments()
        ]);

        const commercialSelect = document.getElementById('selectCommercial');
        const provisionalSelect = document.getElementById('selectProvisional');

        commercialSelect.innerHTML = '<option value="">Seleccionar...</option>' +
            commercial.map(doc => `<option value="${doc.id}">${doc.filename} (${doc.document_type || 'N/A'})</option>`).join('');

        provisionalSelect.innerHTML = '<option value="">Seleccionar...</option>' +
            provisional.map(doc => `<option value="${doc.id}">${doc.filename}</option>`).join('');
    } catch (error) {
        console.error('Error loading documents for comparison:', error);
    }
}

// Display Comparison Result
function displayComparisonResult(comparison) {
    const container = document.getElementById('comparisonResults');
    const result = comparison.comparison_result;

    const statusClass = comparison.status;
    const percentageClass = getPercentageClass(comparison.match_percentage);

    let html = `
        <div class="comparison-result ${statusClass}">
            <div class="row mb-3">
                <div class="col-md-6">
                    <h4>Resultado de Comparación</h4>
                    <p class="mb-0">Estado: <span class="badge bg-${getStatusColor(comparison.status)}">${getStatusText(comparison.status)}</span></p>
                </div>
                <div class="col-md-6 text-end">
                    <div class="match-percentage ${percentageClass}">${comparison.match_percentage.toFixed(1)}%</div>
                    <small class="text-muted">Coincidencia</small>
                </div>
            </div>

            <h5>Detalles de Comparación:</h5>
    `;

    result.comparisons.forEach(comp => {
        const matchClass = comp.match ? 'match' : 'no-match';
        const icon = comp.match ? 'check-circle-fill' : 'x-circle-fill';

        html += `
            <div class="attribute-comparison ${matchClass}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <strong><i class="bi bi-${icon}"></i> ${comp.attribute_name}</strong>
                        ${comp.required ? '<span class="badge bg-primary ms-2">Requerido</span>' : ''}
                        <div class="mt-1">
                            <small>
                                Comercial: <code>${comp.commercial_value}</code><br>
                                Provisorio: <code>${comp.provisional_value}</code>
                            </small>
                        </div>
                    </div>
                    <div class="text-end">
                        <small class="text-muted">${(comp.confidence * 100).toFixed(1)}%</small>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
            <div class="mt-3">
                <small class="text-muted">
                    Comparación realizada: ${new Date(comparison.created_at).toLocaleString()}
                </small>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Display Batch Comparison Results
function displayBatchComparisonResults(batchResult) {
    const container = document.getElementById('comparisonResults');

    let html = `
        <div class="alert alert-info">
            <h5><i class="bi bi-info-circle"></i> ${batchResult.message}</h5>
        </div>
    `;

    batchResult.results.forEach((result, index) => {
        const statusClass = result.status;
        const percentageClass = getPercentageClass(result.match_percentage);

        html += `
            <div class="comparison-result ${statusClass} mb-3">
                <div class="row mb-2">
                    <div class="col-md-8">
                        <h6>Comparación ${index + 1} - Documento Comercial ID: ${result.commercial_document_id}</h6>
                        <span class="badge bg-secondary">${result.commercial_document_type}</span>
                        <span class="badge bg-${getStatusColor(result.status)}">${getStatusText(result.status)}</span>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="match-percentage ${percentageClass}">${result.match_percentage.toFixed(1)}%</div>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="toggleDetails('batch-${index}')">
                    Ver Detalles <i class="bi bi-chevron-down"></i>
                </button>
                <div id="batch-${index}" style="display: none;" class="mt-2">
                    ${result.comparison_details.map(comp => `
                        <div class="attribute-comparison ${comp.match ? 'match' : 'no-match'} mt-2">
                            <strong>${comp.attribute_name}:</strong>
                            Comercial: <code>${comp.commercial_value}</code> |
                            Provisorio: <code>${comp.provisional_value}</code>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function toggleDetails(id) {
    const element = document.getElementById(id);
    element.style.display = element.style.display === 'none' ? 'block' : 'none';
}

// Attributes Setup
function setupAttributes() {
    const form = document.getElementById('attributeForm');
    const defaultsBtn = document.getElementById('createDefaultsBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const attributeData = {
            attribute_name: document.getElementById('attrName').value,
            attribute_key: document.getElementById('attrKey').value,
            description: document.getElementById('attrDescription').value,
            is_required: document.getElementById('attrRequired').checked ? 1 : 0,
            validation_rules: {
                type: document.getElementById('attrType').value
            }
        };

        try {
            await DocumentAPI.createAttribute(attributeData);
            showToast('Atributo creado exitosamente', 'success');
            form.reset();
            loadAttributes();
        } catch (error) {
            showToast(`Error creando atributo: ${error.message}`, 'error');
        }
    });

    defaultsBtn.addEventListener('click', async function() {
        try {
            const result = await DocumentAPI.createDefaultAttributes();
            showToast(result.message, 'success');
            loadAttributes();
        } catch (error) {
            showToast(`Error creando atributos por defecto: ${error.message}`, 'error');
        }
    });
}

// Load Attributes
async function loadAttributes() {
    const container = document.getElementById('attributesList');

    try {
        const attributes = await DocumentAPI.listAttributes();

        if (attributes.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay atributos configurados. Crea algunos o carga los valores por defecto.</p>';
            return;
        }

        container.innerHTML = attributes.map(attr => `
            <div class="attribute-item ${attr.is_required ? 'required' : ''}">
                <div>
                    <strong>${attr.attribute_name}</strong>
                    <small class="text-muted d-block">Clave: ${attr.attribute_key}</small>
                    <small class="text-muted">${attr.description || ''}</small>
                    ${attr.is_required ? '<span class="badge bg-primary ms-2">Requerido</span>' : ''}
                </div>
                <button class="btn btn-sm btn-danger" onclick="deleteAttribute(${attr.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<p class="text-danger">Error cargando atributos: ${error.message}</p>`;
    }
}

// Delete Attribute
async function deleteAttribute(id) {
    showConfirmDelete(
        '¿Estás seguro de que deseas eliminar este atributo?',
        async function() {
            try {
                await DocumentAPI.deleteAttribute(id);
                showToast('Atributo eliminado exitosamente', 'success');
                loadAttributes();
            } catch (error) {
                showToast(`Error eliminando atributo: ${error.message}`, 'error');
            }
        }
    );
}

// Load History
async function loadHistory() {
    const container = document.getElementById('historyList');

    try {
        const comparisons = await DocumentAPI.listComparisons();

        if (comparisons.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay comparaciones en el historial.</p>';
            return;
        }

        container.innerHTML = comparisons.map(comp => {
            const statusClass = comp.status;
            const percentageClass = getPercentageClass(comp.match_percentage);

            return `
                <div class="comparison-result ${statusClass} mb-3">
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Comparación #${comp.id}</h6>
                            <small>
                                Comercial ID: ${comp.commercial_document_id} |
                                Provisorio ID: ${comp.provisional_document_id}
                            </small><br>
                            <span class="badge bg-${getStatusColor(comp.status)}">${getStatusText(comp.status)}</span>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="match-percentage ${percentageClass}">${comp.match_percentage.toFixed(1)}%</div>
                            <small class="text-muted">${new Date(comp.created_at).toLocaleString()}</small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        container.innerHTML = `<p class="text-danger">Error cargando historial: ${error.message}</p>`;
    }
}

// Helper Functions
function showAlert(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="alert alert-${type} alert-custom" role="alert">
            ${message}
        </div>
    `;
    element.style.display = 'block';
}

function hideAlert(elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    element.style.display = 'none';
}

function showProgress(elementId, show) {
    const element = document.getElementById(elementId);
    element.style.display = show ? 'block' : 'none';
}

function getPercentageClass(percentage) {
    if (percentage >= 90) return 'high';
    if (percentage >= 70) return 'medium';
    return 'low';
}

function getStatusColor(status) {
    switch (status) {
        case 'approved': return 'success';
        case 'rejected': return 'danger';
        case 'pending_review': return 'warning';
        default: return 'secondary';
    }
}

function getStatusText(status) {
    switch (status) {
        case 'approved': return 'Aprobado';
        case 'rejected': return 'Rechazado';
        case 'pending_review': return 'Revisión Pendiente';
        default: return status;
    }
}

// View Document Content
async function viewDocumentContent(docId, type) {
    try {
        const endpoint = type === 'commercial'
            ? `/documents/commercial/${docId}/content`
            : `/documents/provisional/${docId}/content`;

        const url = getApiUrl(endpoint);
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error obteniendo contenido del documento');

        const data = await response.json();

        // Mostrar en modal
        showContentModal(data);
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al obtener el contenido del documento: ' + error.message, 'error');
    }
}

function showContentModal(data) {
    const modalHtml = `
        <div class="modal fade" id="contentModal" tabindex="-1" aria-labelledby="contentModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="contentModalLabel">
                            <i class="bi bi-file-text"></i> Contenido del Documento
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <h6><strong>Archivo:</strong> ${data.filename}</h6>
                        ${data.document_type ? `<p><strong>Tipo:</strong> ${data.document_type}</p>` : ''}
                        <hr>
                        <div style="max-height: 500px; overflow-y: auto;">
                            <pre style="white-space: pre-wrap; word-wrap: break-word;">${data.text_content}</pre>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remover modal anterior si existe
    const existingModal = document.getElementById('contentModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('contentModal'));
    modal.show();

    // Limpiar modal al cerrar
    document.getElementById('contentModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}
