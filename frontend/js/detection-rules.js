// Detection Rules Editor
let currentPageType = null;
let currentDocument = null;
let currentPageNumber = 1;
let currentImage = null;
let canvas = null;
let ctx = null;
let isDrawing = false;
let startX = 0;
let startY = 0;
let currentRect = null;
let drawnRects = [];
let canvasZoom = 1.0;
let currentRules = []; // Store current rules for editing
let editingRuleId = null; // Track which rule is being edited

// View detection rules for a page type
async function viewDetectionRules(pageTypeId, displayName) {
    currentPageType = { id: pageTypeId, name: displayName };

    try {
        // Load existing rules
        currentRules = await DocumentAPI.listDetectionRules(pageTypeId);

        // Show rules modal
        showDetectionRulesModal(displayName, currentRules);
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar reglas: ' + error.message, 'error');
    }
}

// Show detection rules modal
function showDetectionRulesModal(pageTypeName, rules) {
    const rulesHtml = rules.length > 0 ? rules.map(rule => `
        <div class="card mb-2">
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${rule.attribute_name}</strong>
                        <br>
                        <small class="text-muted">
                            Coords: (${rule.x1}, ${rule.y1}) → (${rule.x2}, ${rule.y2})
                            <br>
                            Tipo: ${rule.data_type || 'text'} | Comparador: ${rule.comparator || rule.match_type}
                            <br>
                            Valor esperado: ${rule.expected_value || 'N/A'}
                        </small>
                    </div>
                    <div class="btn-group-vertical btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editDetectionRule(${rule.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteDetectionRule(${rule.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('') : '<p class="text-muted">No hay reglas definidas.</p>';

    const existingModal = document.getElementById('detectionRulesModal');

    // Si el modal ya existe, solo actualizar el contenido
    if (existingModal) {
        const rulesListContainer = document.getElementById('rulesList');
        if (rulesListContainer) {
            rulesListContainer.innerHTML = rulesHtml;
            return; // No crear nuevo modal, solo actualizar contenido
        }
    }

    // Si no existe, crear el modal
    const modalHtml = `
        <div class="modal fade" id="detectionRulesModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-rulers"></i> Reglas de Detección - ${pageTypeName}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <button class="btn btn-primary" onclick="showRuleDrawer()">
                                <i class="bi bi-plus-circle"></i> Nueva Regla
                            </button>
                        </div>
                        <div id="rulesList">
                            ${rulesHtml}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('detectionRulesModal'));
    modal.show();

    document.getElementById('detectionRulesModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
        // Limpiar cualquier backdrop que quede
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    });
}

// Show rule drawer (canvas editor)
async function showRuleDrawer(isEdit = false) {
    // Reset editing state for new rules (not when editing)
    if (!isEdit) {
        editingRuleId = null;
    }

    // First, select a document to load images
    const documents = await DocumentAPI.listProvisionalDocuments();

    if (documents.length === 0) {
        showToast('Primero debes subir un documento provisorio para definir reglas', 'warning');
        return;
    }

    const docOptions = documents.map(doc =>
        `<option value="${doc.id}">${doc.filename}</option>`
    ).join('');

    const modalHtml = `
        <div class="modal fade" id="ruleDrawerModal" tabindex="-1">
            <div class="modal-dialog modal-fullscreen">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-pencil-square"></i> Definir Regla de Detección - ${currentPageType.name}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <label class="form-label">Documento de Ejemplo:</label>
                                <select class="form-select" id="ruleDocumentSelect" onchange="loadDocumentForRule()">
                                    <option value="">Seleccionar documento...</option>
                                    ${docOptions}
                                </select>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Página:</label>
                                <div class="input-group">
                                    <button class="btn btn-outline-secondary" onclick="changeRulePage(-1)">
                                        <i class="bi bi-chevron-left"></i>
                                    </button>
                                    <input type="number" class="form-control text-center" id="rulePageNumber"
                                           value="1" min="1" readonly>
                                    <button class="btn btn-outline-secondary" onclick="changeRulePage(1)">
                                        <i class="bi bi-chevron-right"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Instrucciones:</label>
                                <p class="small text-muted mb-0">
                                    Haz clic y arrastra sobre la imagen para dibujar el área donde se debe buscar el texto.
                                </p>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-2">
                                    <div class="btn-group" role="group">
                                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="zoomRuleCanvas(-0.1)" title="Alejar">
                                            <i class="bi bi-zoom-out"></i> -
                                        </button>
                                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="resetRuleZoom()" title="Restablecer zoom" id="ruleZoomLevelBtn">
                                            100%
                                        </button>
                                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="zoomRuleCanvas(0.1)" title="Acercar">
                                            <i class="bi bi-zoom-in"></i> +
                                        </button>
                                    </div>
                                </div>
                                <div class="border" id="canvasContainer" style="overflow: auto; max-height: 70vh; background: #f5f5f5;">
                                    <canvas id="ruleCanvas" style="cursor: crosshair; display: block;"></canvas>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-header">
                                        <strong>Configuración de Regla</strong>
                                    </div>
                                    <div class="card-body">
                                        <form id="ruleConfigForm">
                                            <div class="mb-3">
                                                <label for="ruleAttrName" class="form-label">Nombre del Atributo*</label>
                                                <input type="text" class="form-control" id="ruleAttrName" required
                                                       placeholder="ej: tipo_documento">
                                            </div>
                                            <div class="mb-3">
                                                <label for="ruleDataType" class="form-label">Tipo de Dato</label>
                                                <select class="form-select" id="ruleDataType" onchange="updateComparatorOptions()">
                                                    <option value="text">Texto</option>
                                                    <option value="number">Número</option>
                                                    <option value="date">Fecha</option>
                                                </select>
                                            </div>
                                            <div class="mb-3">
                                                <label for="ruleComparator" class="form-label">Comparador</label>
                                                <select class="form-select" id="ruleComparator">
                                                    <option value="contains">Contiene</option>
                                                    <option value="not_contains">No Contiene</option>
                                                    <option value="exact">Exacto</option>
                                                    <option value="not_exact">No Igual</option>
                                                    <option value="regex">Expresión Regular</option>
                                                </select>
                                            </div>
                                            <div class="mb-3">
                                                <label for="ruleExpectedValue" class="form-label">Valor de Referencia</label>
                                                <input type="text" class="form-control" id="ruleExpectedValue"
                                                       placeholder="ej: PROVISORIO">
                                                <small class="text-muted" id="ruleExpectedValueHint"></small>
                                            </div>
                                            <div class="mb-3" id="ruleDateFormatGroup" style="display: none;">
                                                <label for="ruleDateFormat" class="form-label">Formato de Fecha</label>
                                                <input type="text" class="form-control" id="ruleDateFormat"
                                                       placeholder="ej: %d/%m/%Y">
                                                <small class="text-muted">Formato Python strptime (ej: %d/%m/%Y para 31/12/2023)</small>
                                            </div>
                                            <div class="mb-3">
                                                <label for="rulePriority" class="form-label">Prioridad</label>
                                                <input type="number" class="form-control" id="rulePriority"
                                                       value="0" min="0" max="100">
                                                <small class="text-muted">Mayor valor = mayor prioridad</small>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">Coordenadas</label>
                                                <div class="small text-muted" id="ruleCoordinates">
                                                    Dibuja un rectángulo en la imagen
                                                </div>
                                            </div>
                                            <hr>
                                            <button type="button" class="btn btn-danger btn-sm w-100 mb-2"
                                                    onclick="clearRuleCanvas()">
                                                <i class="bi bi-x-circle"></i> Limpiar Área
                                            </button>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="saveDetectionRule()">
                            <i class="bi bi-save"></i> Guardar Regla
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    const existingModal = document.getElementById('ruleDrawerModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('ruleDrawerModal'));
    modal.show();

    // Initialize canvas
    canvas = document.getElementById('ruleCanvas');
    ctx = canvas.getContext('2d');

    // Setup mouse events
    setupCanvasEvents();

    document.getElementById('ruleDrawerModal').addEventListener('hidden.bs.modal', function () {
        currentDocument = null;
        currentPageNumber = 1;
        currentImage = null;
        currentRect = null;
        drawnRects = [];
        this.remove();
    });
}

// Setup canvas mouse events
function setupCanvasEvents() {
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
}

function startDrawing(e) {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
}

function draw(e) {
    if (!isDrawing) return;

    const rect = canvas.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    // Redraw image with zoom
    if (currentImage) {
        ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);
    }

    // Draw existing rects with zoom
    drawnRects.forEach(r => {
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 2;
        ctx.strokeRect(r.x * canvasZoom, r.y * canvasZoom, r.width * canvasZoom, r.height * canvasZoom);
    });

    // Draw current rect
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 2;
    ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
}

function stopDrawing(e) {
    if (!isDrawing) return;
    isDrawing = false;

    const rect = canvas.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    const width = endX - startX;
    const height = endY - startY;

    if (Math.abs(width) > 5 && Math.abs(height) > 5) {
        // Normalize coordinates and convert to original image coordinates (removing zoom)
        const x1 = Math.min(startX, endX) / canvasZoom;
        const y1 = Math.min(startY, endY) / canvasZoom;
        const x2 = Math.max(startX, endX) / canvasZoom;
        const y2 = Math.max(startY, endY) / canvasZoom;

        currentRect = { x1: Math.round(x1), y1: Math.round(y1), x2: Math.round(x2), y2: Math.round(y2) };

        // Update coordinates display
        document.getElementById('ruleCoordinates').textContent =
            `X1: ${currentRect.x1}, Y1: ${currentRect.y1}, X2: ${currentRect.x2}, Y2: ${currentRect.y2}`;
    }
}

function clearRuleCanvas() {
    currentRect = null;
    drawnRects = [];
    updateRuleCanvas();
    document.getElementById('ruleCoordinates').textContent = 'Dibuja un rectángulo en la imagen';
}

// Load document for rule
async function loadDocumentForRule() {
    const docId = document.getElementById('ruleDocumentSelect').value;
    if (!docId) return;

    try {
        currentDocument = docId;
        currentPageNumber = 1;
        document.getElementById('rulePageNumber').value = 1;
        await loadRulePageImage();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar documento: ' + error.message, 'error');
    }
}

// Change page
function changeRulePage(delta) {
    currentPageNumber += delta;
    if (currentPageNumber < 1) currentPageNumber = 1;
    document.getElementById('rulePageNumber').value = currentPageNumber;
    loadRulePageImage();
}

// Load page image
async function loadRulePageImage() {
    if (!currentDocument) return;

    const imageUrl = DocumentAPI.getProvisionalDocumentImageUrl(currentDocument, currentPageNumber);

    const img = new Image();
    img.onload = function() {
        currentImage = img;
        canvas.width = img.width * canvasZoom;
        canvas.height = img.height * canvasZoom;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        clearRuleCanvas();
    };
    img.onerror = function() {
        showToast('No hay imagen para la página ' + currentPageNumber, 'warning');
        currentPageNumber--;
        document.getElementById('rulePageNumber').value = currentPageNumber;
    };
    img.src = imageUrl;
}

// Save detection rule
async function saveDetectionRule() {
    const form = document.getElementById('ruleConfigForm');

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    if (!currentRect) {
        showToast('Debes dibujar un área en la imagen', 'warning');
        return;
    }

    const dataType = document.getElementById('ruleDataType').value;
    const ruleData = {
        page_type_id: currentPageType.id,
        attribute_name: document.getElementById('ruleAttrName').value,
        x1: currentRect.x1,
        y1: currentRect.y1,
        x2: currentRect.x2,
        y2: currentRect.y2,
        expected_value: document.getElementById('ruleExpectedValue').value || null,
        data_type: dataType,
        comparator: document.getElementById('ruleComparator').value,
        match_type: document.getElementById('ruleComparator').value, // Mantener compatibilidad
        date_format: dataType === 'date' ? (document.getElementById('ruleDateFormat').value || null) : null,
        priority: parseInt(document.getElementById('rulePriority').value)
    };

    try {
        await DocumentAPI.createDetectionRule(currentPageType.id, ruleData);
        showToast('Regla creada exitosamente', 'success');

        // Close drawer modal and wait for it to fully close
        const drawerModal = bootstrap.Modal.getInstance(document.getElementById('ruleDrawerModal'));
        const modalElement = document.getElementById('ruleDrawerModal');

        // Wait for modal to be hidden before opening the next one
        modalElement.addEventListener('hidden.bs.modal', function onHidden() {
            // Remove listener to avoid multiple calls
            modalElement.removeEventListener('hidden.bs.modal', onHidden);

            // Reload rules in the main modal
            viewDetectionRules(currentPageType.id, currentPageType.name);
        });

        drawerModal.hide();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al crear regla: ' + error.message, 'error');
    }
}

// Edit detection rule
async function editDetectionRule(ruleId) {
    // Find the rule in currentRules
    const rule = currentRules.find(r => r.id === ruleId);
    if (!rule) {
        showToast('No se encontró la regla', 'error');
        return;
    }

    editingRuleId = ruleId;

    // Pre-fill the form with existing values
    await showRuleDrawer(true); // Pass true to indicate this is an edit

    // Wait for modal to be visible
    setTimeout(() => {
        // Set form values
        document.getElementById('ruleAttrName').value = rule.attribute_name;
        document.getElementById('ruleExpectedValue').value = rule.expected_value || '';
        document.getElementById('ruleDataType').value = rule.data_type || 'text';
        document.getElementById('rulePriority').value = rule.priority || 0;

        // Update comparator options for the data type
        updateComparatorOptions();

        // Set comparator value after options are updated
        document.getElementById('ruleComparator').value = rule.comparator || rule.match_type || 'contains';

        // Set date format if applicable
        if (rule.date_format) {
            document.getElementById('ruleDateFormat').value = rule.date_format;
        }

        // Set coordinates
        currentRect = {
            x1: rule.x1,
            y1: rule.y1,
            x2: rule.x2,
            y2: rule.y2
        };

        // Update coordinates display
        document.getElementById('ruleCoordinates').textContent =
            `X1: ${rule.x1}, Y1: ${rule.y1}, X2: ${rule.x2}, Y2: ${rule.y2}`;

        // Update modal title
        const modalTitle = document.querySelector('#ruleDrawerModal .modal-title');
        if (modalTitle) {
            modalTitle.innerHTML = '<i class="bi bi-pencil-square"></i> Editar Regla de Detección - ' + currentPageType.name;
        }

        // Update save button text
        const saveBtn = document.querySelector('#ruleDrawerModal .modal-footer .btn-primary');
        if (saveBtn) {
            saveBtn.innerHTML = '<i class="bi bi-save"></i> Actualizar Regla';
            saveBtn.onclick = updateDetectionRule;
        }
    }, 300);
}

// Update detection rule
async function updateDetectionRule() {
    const form = document.getElementById('ruleConfigForm');

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    if (!currentRect) {
        showToast('Debes dibujar un área en la imagen', 'warning');
        return;
    }

    const dataType = document.getElementById('ruleDataType').value;
    const ruleData = {
        attribute_name: document.getElementById('ruleAttrName').value,
        x1: currentRect.x1,
        y1: currentRect.y1,
        x2: currentRect.x2,
        y2: currentRect.y2,
        expected_value: document.getElementById('ruleExpectedValue').value || null,
        data_type: dataType,
        comparator: document.getElementById('ruleComparator').value,
        match_type: document.getElementById('ruleComparator').value, // Mantener compatibilidad
        date_format: dataType === 'date' ? (document.getElementById('ruleDateFormat').value || null) : null,
        priority: parseInt(document.getElementById('rulePriority').value)
    };

    try {
        await DocumentAPI.updateDetectionRule(editingRuleId, ruleData);
        showToast('Regla actualizada exitosamente', 'success');

        editingRuleId = null;

        // Close drawer modal and wait for it to fully close
        const drawerModal = bootstrap.Modal.getInstance(document.getElementById('ruleDrawerModal'));
        const modalElement = document.getElementById('ruleDrawerModal');

        modalElement.addEventListener('hidden.bs.modal', function onHidden() {
            modalElement.removeEventListener('hidden.bs.modal', onHidden);
            viewDetectionRules(currentPageType.id, currentPageType.name);
        });

        drawerModal.hide();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al actualizar regla: ' + error.message, 'error');
    }
}

// Delete detection rule
async function deleteDetectionRule(ruleId) {
    if (!confirm('¿Está seguro de eliminar esta regla?')) {
        return;
    }

    try {
        await DocumentAPI.deleteDetectionRule(ruleId);
        showToast('Regla eliminada exitosamente', 'success');

        // Reload rules
        viewDetectionRules(currentPageType.id, currentPageType.name);
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar regla: ' + error.message, 'error');
    }
}

// Zoom functions
function zoomRuleCanvas(delta) {
    canvasZoom += delta;

    // Limitar el zoom entre 0.2x y 10x
    if (canvasZoom < 0.2) {
        canvasZoom = 0.2;
    } else if (canvasZoom > 10.0) {
        canvasZoom = 10.0;
    }

    updateRuleCanvas();
}

function resetRuleZoom() {
    canvasZoom = 1.0;
    updateRuleCanvas();
}

function updateRuleCanvas() {
    if (!currentImage) return;

    // Update canvas size with zoom
    canvas.width = currentImage.width * canvasZoom;
    canvas.height = currentImage.height * canvasZoom;

    // Redraw everything
    ctx.drawImage(currentImage, 0, 0, canvas.width, canvas.height);

    // Redraw rectangles with zoom
    drawnRects.forEach(r => {
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 2;
        ctx.strokeRect(r.x * canvasZoom, r.y * canvasZoom, r.width * canvasZoom, r.height * canvasZoom);
    });

    if (currentRect) {
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        const width = (currentRect.x2 - currentRect.x1) * canvasZoom;
        const height = (currentRect.y2 - currentRect.y1) * canvasZoom;
        ctx.strokeRect(currentRect.x1 * canvasZoom, currentRect.y1 * canvasZoom, width, height);
    }

    // Update zoom display
    const zoomBtn = document.getElementById('ruleZoomLevelBtn');
    if (zoomBtn) {
        zoomBtn.textContent = `${Math.round(canvasZoom * 100)}%`;
    }
}

// Update comparator options based on data type
function updateComparatorOptions() {
    const dataType = document.getElementById('ruleDataType').value;
    const comparatorSelect = document.getElementById('ruleComparator');
    const dateFormatGroup = document.getElementById('ruleDateFormatGroup');
    const valueHint = document.getElementById('ruleExpectedValueHint');

    // Clear current options
    comparatorSelect.innerHTML = '';

    if (dataType === 'text') {
        // Text comparators
        comparatorSelect.innerHTML = `
            <option value="contains">Contiene</option>
            <option value="not_contains">No Contiene</option>
            <option value="exact">Exacto</option>
            <option value="not_exact">No Igual</option>
            <option value="regex">Expresión Regular</option>
        `;
        dateFormatGroup.style.display = 'none';
        valueHint.textContent = 'Texto a buscar o regex';
    } else if (dataType === 'number') {
        // Number comparators
        comparatorSelect.innerHTML = `
            <option value="eq">Igual (=)</option>
            <option value="ne">Distinto (≠)</option>
            <option value="gt">Mayor (&gt;)</option>
            <option value="lt">Menor (&lt;)</option>
            <option value="gte">Mayor o Igual (≥)</option>
            <option value="lte">Menor o Igual (≤)</option>
        `;
        dateFormatGroup.style.display = 'none';
        valueHint.textContent = 'Número a comparar (ej: 1000.50)';
    } else if (dataType === 'date') {
        // Date comparators
        comparatorSelect.innerHTML = `
            <option value="eq">Igual (=)</option>
            <option value="ne">Distinto (≠)</option>
            <option value="gt">Mayor (después de)</option>
            <option value="lt">Menor (antes de)</option>
            <option value="gte">Mayor o Igual</option>
            <option value="lte">Menor o Igual</option>
        `;
        dateFormatGroup.style.display = 'block';
        valueHint.textContent = 'Fecha a comparar en el formato especificado';
    }
}
