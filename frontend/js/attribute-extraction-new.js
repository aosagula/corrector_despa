// Attribute Extraction Configuration - Integrated UI
let selectedPageType = null;
let selectedDocument = null;
let selectedPageNumber = 1;
let attributeCanvas = null;
let attributeCtx = null;
let attributeImage = null;
let attributeZoom = 0.4; // Default zoom 40%
let isDrawingAttribute = false;
let drawStartX = 0;
let drawStartY = 0;
let currentAttributeBox = null;
let configuredAttributes = [];
let editingAttributeIndex = null;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let panOffsetX = 0;
let panOffsetY = 0;
let detectedPageType = null;
let allPageDetections = []; // Almacena todas las detecciones de páginas
let matchingPages = []; // Páginas que coinciden con el tipo seleccionado
let currentPageIndex = 0; // Índice actual en matchingPages

// Main function to show the attribute configuration screen
async function showAttributeConfiguration() {
    const container = document.getElementById('attribute-config-content');
    if (!container) {
        console.error('Container attribute-config-content not found');
        return;
    }

    try {
        // Get page types
        const pageTypes = await DocumentAPI.listPageTypes();
        if (pageTypes.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> Primero debes crear tipos de páginas.
                    <br>
                    <a href="../pages/page-types.html" class="btn btn-sm btn-primary mt-2">
                        <i class="bi bi-plus-circle"></i> Crear Tipos de Páginas
                    </a>
                </div>
            `;
            return;
        }

        // Get documents
        const documents = await DocumentAPI.listProvisionalDocuments();
        if (documents.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> Primero debes subir documentos provisorios.
                    <br>
                    <a href="../pages/upload-provisional.html" class="btn btn-sm btn-primary mt-2">
                        <i class="bi bi-upload"></i> Subir Documento Provisorio
                    </a>
                </div>
            `;
            return;
        }

        const pageTypeOptions = pageTypes.map(pt =>
            `<option value="${pt.id}" data-name="${pt.name}">${pt.display_name}</option>`
        ).join('');

        const documentOptions = documents.map(doc =>
            `<option value="${doc.id}">${doc.filename}</option>`
        ).join('');

        const contentHtml = `
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label"><strong>Documento Provisorio:</strong></label>
                                    <select class="form-select" id="documentSelector" onchange="onDocumentSelected()">
                                        <option value="">Seleccionar documento...</option>
                                        ${documentOptions}
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label"><strong>Tipo de Página:</strong></label>
                                    <select class="form-select" id="pageTypeSelector" onchange="loadPageTypeData()" disabled>
                                        <option value="">Primero selecciona un documento...</option>
                                        ${pageTypeOptions}
                                    </select>
                                    <small class="text-muted">Selecciona primero un documento provisorio</small>
                                </div>
                            </div>

                            <div id="configurationPanel" style="display: none;">
                                <div class="row">
                                    <!-- Canvas Area (Left) -->
                                    <div class="col-md-9">
                                        <div class="card">
                                            <div class="card-header d-flex justify-content-between">
                                                <span><strong>Imagen de Ejemplo</strong></span>
                                                <div class="btn-group btn-group-sm">
                                                    <button class="btn btn-outline-secondary" onclick="changeAttributeZoom(-0.1)">
                                                        <i class="bi bi-zoom-out"></i>
                                                    </button>
                                                    <button class="btn btn-outline-secondary" id="attrZoomDisplay">40%</button>
                                                    <button class="btn btn-outline-secondary" onclick="changeAttributeZoom(0.1)">
                                                        <i class="bi bi-zoom-in"></i>
                                                    </button>
                                                </div>
                                            </div>
                                            <div class="card-body p-0">
                                                <div class="border" id="canvasContainer" style="overflow: auto; max-height: 65vh; background: #f5f5f5; position: relative;">
                                                    <canvas id="attributeCanvas" style="display: block;"></canvas>
                                                </div>
                                                <div class="card-text p-2 small text-muted">
                                                    <i class="bi bi-info-circle"></i>
                                                    <strong>Espacio:</strong> Mantener presionado para panear |
                                                    <strong>Mouse:</strong> Arrastrar para dibujar área
                                                </div>
                                            </div>
                                            <div class="card-footer">
                                                <div class="d-flex justify-content-between">
                                                    <button class="btn btn-sm btn-secondary" onclick="navigateAttributePage(-1)">
                                                        <i class="bi bi-chevron-left"></i> Anterior
                                                    </button>
                                                    <span id="pageIndicator">Página 1</span>
                                                    <button class="btn btn-sm btn-secondary" onclick="navigateAttributePage(1)">
                                                        Siguiente <i class="bi bi-chevron-right"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Configuration Panel (Right) -->
                                    <div class="col-md-3">
                                        <div class="card mb-3">
                                            <div class="card-header">
                                                <strong>Definir Nuevo Atributo</strong>
                                            </div>
                                            <div class="card-body">
                                                <form id="attributeDefinitionForm">
                                                    <div class="mb-3">
                                                        <label class="form-label">Nombre del Atributo*</label>
                                                        <input type="text" class="form-control" id="attrNameDef" required
                                                               placeholder="ej: numero_despacho">
                                                    </div>
                                                    <div class="mb-3">
                                                        <label class="form-label">Descripción</label>
                                                        <textarea class="form-control" id="attrDescriptionDef" rows="2"
                                                                  placeholder="Descripción del atributo"></textarea>
                                                    </div>
                                                    <div class="mb-3">
                                                        <label class="form-label">Tipo de Dato*</label>
                                                        <select class="form-select" id="attrDataType" required>
                                                            <option value="text">Texto</option>
                                                            <option value="number">Número</option>
                                                            <option value="date">Fecha</option>
                                                        </select>
                                                    </div>
                                                    <div class="mb-3">
                                                        <label class="form-label">Área de Extracción</label>
                                                        <div class="small text-muted" id="attrCoordinates">
                                                            Dibuja un rectángulo en la imagen
                                                        </div>
                                                    </div>
                                                    <div class="d-grid gap-2">
                                                        <button type="button" class="btn btn-danger btn-sm" onclick="clearAttributeBox()">
                                                            <i class="bi bi-x-circle"></i> Limpiar Área
                                                        </button>
                                                        <button type="button" class="btn btn-primary" onclick="saveAttribute()">
                                                            <i class="bi bi-plus-circle"></i> Agregar Atributo
                                                        </button>
                                                    </div>
                                                </form>
                                            </div>
                                        </div>

                                        <!-- List of configured attributes -->
                                        <div class="card">
                                            <div class="card-header">
                                                <strong>Atributos Configurados</strong>
                                                <span class="badge bg-primary float-end" id="attrCount">0</span>
                                            </div>
                                            <div class="card-body" id="configuredAttributesList" style="max-height: 30vh; overflow-y: auto;">
                                                <p class="text-muted small">No hay atributos configurados</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                <div class="mt-3">
                    <button type="button" class="btn btn-success" onclick="saveAllAttributes()" id="saveAllBtn" disabled>
                        <i class="bi bi-save"></i> Guardar Todos los Atributos
                    </button>
                </div>
        `;

        container.innerHTML = contentHtml;

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> Error al cargar la configuración: ${error.message}
            </div>
        `;
    }
}

// When document is selected
async function onDocumentSelected() {
    const docSelector = document.getElementById('documentSelector');
    const pageTypeSelector = document.getElementById('pageTypeSelector');

    if (!docSelector.value) {
        pageTypeSelector.value = '';
        pageTypeSelector.disabled = true;
        pageTypeSelector.options[0].text = 'Primero selecciona un documento...';
        document.getElementById('configurationPanel').style.display = 'none';
        // Reset state
        allPageDetections = [];
        matchingPages = [];
        currentPageIndex = 0;
        return;
    }

    selectedDocument = parseInt(docSelector.value);
    selectedPageNumber = 1;

    // Enable page type selector
    pageTypeSelector.disabled = false;
    pageTypeSelector.options[0].text = 'Seleccionar tipo de página...';
    pageTypeSelector.style.borderColor = '#198754';
    pageTypeSelector.style.boxShadow = '0 0 5px rgba(25, 135, 84, 0.3)';
    setTimeout(() => {
        pageTypeSelector.style.borderColor = '';
        pageTypeSelector.style.boxShadow = '';
    }, 1000);

    // Reset page detection state
    allPageDetections = [];
    matchingPages = [];
    currentPageIndex = 0;

    showToast('✓ Documento seleccionado. Ahora elige un tipo de página', 'success');

    // If a page type is already selected, reload with new document
    if (pageTypeSelector.value) {
        await loadPageTypeData();
    }
}

// Load data when page type is selected
async function loadPageTypeData() {
    const selector = document.getElementById('pageTypeSelector');
    const docSelector = document.getElementById('documentSelector');
    const pageTypeId = selector.value;

    if (!pageTypeId) {
        document.getElementById('configurationPanel').style.display = 'none';
        return;
    }

    if (!selectedDocument) {
        showToast('⚠️ Primero debes seleccionar un documento provisorio', 'warning');
        // Reset page type selector to force user to select document first
        selector.value = '';
        // Highlight document selector with animation
        docSelector.style.transition = 'all 0.3s ease';
        docSelector.style.borderColor = '#ffc107';
        docSelector.style.borderWidth = '3px';
        docSelector.style.boxShadow = '0 0 10px rgba(255, 193, 7, 0.5)';
        docSelector.focus();

        // Scroll to document selector
        docSelector.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(() => {
            docSelector.style.borderColor = '';
            docSelector.style.borderWidth = '';
            docSelector.style.boxShadow = '';
        }, 3000);
        return;
    }

    try {
        selectedPageType = {
            id: parseInt(pageTypeId),
            name: selector.options[selector.selectedIndex].getAttribute('data-name'),
            display_name: selector.options[selector.selectedIndex].textContent
        };

        // Detect all pages of the selected document
        showToast('Detectando tipos de páginas del documento...', 'info');
        const detectionResponse = await fetch(getApiUrl(`/documents/provisional/${selectedDocument}/detect-pages`));
        if (!detectionResponse.ok) {
            throw new Error('Error detectando páginas');
        }

        const detectionData = await detectionResponse.json();
        allPageDetections = detectionData.pages || [];

        // Filter pages that match the selected page type
        matchingPages = allPageDetections.filter(page => {
            return page.page_type_id === selectedPageType.id;
        });

        if (matchingPages.length === 0) {
            showToast(`No se encontraron páginas del tipo "${selectedPageType.display_name}" en este documento`, 'warning');
            document.getElementById('configurationPanel').style.display = 'none';
            return;
        }

        showToast(`Se encontraron ${matchingPages.length} página(s) del tipo "${selectedPageType.display_name}"`, 'success');

        // Load existing attributes for this page type
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}/extraction-coordinates`));
        configuredAttributes = response.ok ? await response.json() : [];

        // Set to first matching page
        currentPageIndex = 0;
        selectedPageNumber = matchingPages[0].page_number;

        // Display configuration panel
        document.getElementById('configurationPanel').style.display = 'block';

        // Initialize canvas
        attributeCanvas = document.getElementById('attributeCanvas');
        attributeCtx = attributeCanvas.getContext('2d');
        attributeCanvas.style.cursor = 'crosshair';
        setupCanvasListeners();

        // Load the first matching page
        await loadPageImage();

        // Display configured attributes
        displayConfiguredAttributes();

    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar datos: ' + error.message, 'error');
    }
}

// Load the current page image
async function loadPageImage() {
    if (!selectedDocument || matchingPages.length === 0) return;

    const imageUrl = DocumentAPI.getProvisionalDocumentImageUrl(selectedDocument, selectedPageNumber);

    const img = new Image();
    img.onload = function() {
        attributeImage = img;
        attributeCanvas.width = img.width * attributeZoom;
        attributeCanvas.height = img.height * attributeZoom;
        panOffsetX = 0;
        panOffsetY = 0;
        redrawCanvas();

        // Update page indicator with more info
        const currentPage = matchingPages[currentPageIndex];
        const confidence = currentPage.detected_type ? (currentPage.detected_type.confidence * 100).toFixed(1) : 0;
        document.getElementById('pageIndicator').innerHTML = `
            Página ${selectedPageNumber} de ${matchingPages.length}
            <span class="badge bg-info">${selectedPageType.display_name}</span>
            <small class="text-muted">(${confidence}% confianza)</small>
        `;
    };
    img.onerror = function() {
        showToast('Error al cargar imagen de página ' + selectedPageNumber, 'error');
    };
    img.src = imageUrl;
}

// Navigate between pages (only matching pages)
async function navigateAttributePage(delta) {
    if (matchingPages.length === 0) return;

    currentPageIndex += delta;

    // Loop around
    if (currentPageIndex < 0) {
        currentPageIndex = matchingPages.length - 1;
    } else if (currentPageIndex >= matchingPages.length) {
        currentPageIndex = 0;
    }

    selectedPageNumber = matchingPages[currentPageIndex].page_number;
    await loadPageImage();
}

// Setup canvas event listeners
function setupCanvasListeners() {
    attributeCanvas.addEventListener('mousedown', onCanvasMouseDown);
    attributeCanvas.addEventListener('mousemove', onCanvasMouseMove);
    attributeCanvas.addEventListener('mouseup', onCanvasMouseUp);
    attributeCanvas.addEventListener('mouseout', onCanvasMouseUp);

    // Listen for spacebar for panning
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
}

let spacePressed = false;

function onKeyDown(e) {
    if (e.code === 'Space' && !spacePressed) {
        spacePressed = true;
        attributeCanvas.style.cursor = 'grab';
        e.preventDefault();
    }
}

function onKeyUp(e) {
    if (e.code === 'Space') {
        spacePressed = false;
        attributeCanvas.style.cursor = isPanning ? 'grabbing' : 'crosshair';
        if (isPanning) {
            isPanning = false;
        }
    }
}

function onCanvasMouseDown(e) {
    const rect = attributeCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (spacePressed) {
        // Start panning
        isPanning = true;
        panStartX = e.clientX;
        panStartY = e.clientY;
        attributeCanvas.style.cursor = 'grabbing';
    } else {
        // Start drawing
        isDrawingAttribute = true;
        drawStartX = x;
        drawStartY = y;
    }
}

function onCanvasMouseMove(e) {
    if (isPanning) {
        // Pan the canvas container
        const container = document.getElementById('canvasContainer');
        const dx = e.clientX - panStartX;
        const dy = e.clientY - panStartY;

        container.scrollLeft -= dx;
        container.scrollTop -= dy;

        panStartX = e.clientX;
        panStartY = e.clientY;
        return;
    }

    if (!isDrawingAttribute) return;

    const rect = attributeCanvas.getBoundingClientRect();
    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    redrawCanvas();

    // Draw current rectangle
    attributeCtx.strokeStyle = '#28a745';
    attributeCtx.lineWidth = 3;
    attributeCtx.strokeRect(drawStartX, drawStartY, currentX - drawStartX, currentY - drawStartY);
}

function onCanvasMouseUp(e) {
    if (isPanning) {
        isPanning = false;
        attributeCanvas.style.cursor = spacePressed ? 'grab' : 'crosshair';
        return;
    }

    if (!isDrawingAttribute) return;
    isDrawingAttribute = false;

    const rect = attributeCanvas.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    const width = endX - drawStartX;
    const height = endY - drawStartY;

    if (Math.abs(width) > 5 && Math.abs(height) > 5) {
        const x1 = Math.min(drawStartX, endX) / attributeZoom;
        const y1 = Math.min(drawStartY, endY) / attributeZoom;
        const x2 = Math.max(drawStartX, endX) / attributeZoom;
        const y2 = Math.max(drawStartY, endY) / attributeZoom;

        currentAttributeBox = {
            x1: Math.round(x1),
            y1: Math.round(y1),
            x2: Math.round(x2),
            y2: Math.round(y2)
        };

        document.getElementById('attrCoordinates').innerHTML = `
            <span class="badge bg-success">
                (${currentAttributeBox.x1}, ${currentAttributeBox.y1}) → (${currentAttributeBox.x2}, ${currentAttributeBox.y2})
            </span>
        `;

        redrawCanvas();
    }
}

// Redraw canvas with image and boxes
function redrawCanvas() {
    if (!attributeImage) return;

    // Clear and draw image
    attributeCtx.clearRect(0, 0, attributeCanvas.width, attributeCanvas.height);
    attributeCtx.drawImage(attributeImage, 0, 0, attributeCanvas.width, attributeCanvas.height);

    // Draw existing attribute boxes
    configuredAttributes.forEach((attr, index) => {
        const color = index === editingAttributeIndex ? '#ffc107' : '#007bff';
        attributeCtx.strokeStyle = color;
        attributeCtx.lineWidth = 2;
        attributeCtx.strokeRect(
            attr.x1 * attributeZoom,
            attr.y1 * attributeZoom,
            (attr.x2 - attr.x1) * attributeZoom,
            (attr.y2 - attr.y1) * attributeZoom
        );

        // Draw label
        attributeCtx.fillStyle = color;
        attributeCtx.font = `${12 * attributeZoom}px Arial`;
        attributeCtx.fillText(attr.label || attr.name, attr.x1 * attributeZoom + 5, attr.y1 * attributeZoom - 5);
    });

    // Draw current box being defined
    if (currentAttributeBox) {
        attributeCtx.strokeStyle = '#28a745';
        attributeCtx.lineWidth = 3;
        attributeCtx.strokeRect(
            currentAttributeBox.x1 * attributeZoom,
            currentAttributeBox.y1 * attributeZoom,
            (currentAttributeBox.x2 - currentAttributeBox.x1) * attributeZoom,
            (currentAttributeBox.y2 - currentAttributeBox.y1) * attributeZoom
        );
    }
}

// Clear current attribute box
function clearAttributeBox() {
    currentAttributeBox = null;
    document.getElementById('attrCoordinates').innerHTML = 'Dibuja un rectángulo en la imagen';
    redrawCanvas();
}

// Change zoom
function changeAttributeZoom(delta) {
    attributeZoom += delta;
    if (attributeZoom < 0.2) attributeZoom = 0.2;
    if (attributeZoom > 10) attributeZoom = 10;

    document.getElementById('attrZoomDisplay').textContent = `${Math.round(attributeZoom * 100)}%`;

    if (attributeImage) {
        attributeCanvas.width = attributeImage.width * attributeZoom;
        attributeCanvas.height = attributeImage.height * attributeZoom;
        redrawCanvas();
    }
}

// Save attribute to local list (or update if editing)
async function saveAttribute() {
    const form = document.getElementById('attributeDefinitionForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    if (!currentAttributeBox) {
        showToast('Debes dibujar un área en la imagen', 'warning');
        return;
    }

    // Validate coordinates
    if (currentAttributeBox.x2 <= 0 || currentAttributeBox.y2 <= 0) {
        showToast('Las coordenadas deben ser mayores que 0', 'error');
        return;
    }

    const attributeData = {
        page_type_id: selectedPageType.id,
        label: document.getElementById('attrNameDef').value,
        description: document.getElementById('attrDescriptionDef').value || null,
        data_type: document.getElementById('attrDataType').value,
        x1: Math.max(0, currentAttributeBox.x1),
        y1: Math.max(0, currentAttributeBox.y1),
        x2: Math.max(1, currentAttributeBox.x2),
        y2: Math.max(1, currentAttributeBox.y2)
    };

    if (editingAttributeIndex !== null) {
        // Update existing attribute
        const existingAttr = configuredAttributes[editingAttributeIndex];

        if (existingAttr._isNew) {
            // Just update locally
            configuredAttributes[editingAttributeIndex] = {
                ...attributeData,
                _isNew: true
            };
            showToast('Atributo actualizado en la lista', 'success');
        } else {
            // Update in database
            try {
                await DocumentAPI.updateCoordinate(existingAttr.id, {
                    label: attributeData.label,
                    description: attributeData.description,
                    data_type: attributeData.data_type,
                    x1: attributeData.x1,
                    y1: attributeData.y1,
                    x2: attributeData.x2,
                    y2: attributeData.y2
                });

                // Update locally
                configuredAttributes[editingAttributeIndex] = {
                    ...existingAttr,
                    ...attributeData
                };

                showToast('Atributo actualizado en la base de datos', 'success');
            } catch (error) {
                showToast('Error al actualizar: ' + error.message, 'error');
                return;
            }
        }

        // Reset editing state
        cancelEditAttribute();
    } else {
        // Add new attribute
        configuredAttributes.push({
            ...attributeData,
            _isNew: true  // Mark as new (not saved to DB yet)
        });

        showToast('Atributo agregado a la lista', 'success');
    }

    // Clear form
    form.reset();
    clearAttributeBox();

    // Update display
    displayConfiguredAttributes();
}

// Display configured attributes
function displayConfiguredAttributes() {
    const container = document.getElementById('configuredAttributesList');
    const countBadge = document.getElementById('attrCount');

    countBadge.textContent = configuredAttributes.length;

    if (configuredAttributes.length === 0) {
        container.innerHTML = '<p class="text-muted small">No hay atributos configurados</p>';
        document.getElementById('saveAllBtn').disabled = true;
        return;
    }

    const html = configuredAttributes.map((attr, index) => {
        const badge = attr._isNew ? '<span class="badge bg-warning text-dark ms-2">Nuevo</span>' : '<span class="badge bg-success text-white ms-2">Guardado</span>';
        const statusClass = attr._isNew ? 'border-warning' : 'border-success';
        return `
            <div class="card mb-2 ${statusClass}">
                <div class="card-body p-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong>${attr.label}</strong> ${badge}
                            <br>
                            <small class="text-muted">
                                Tipo: ${attr.data_type || 'text'}
                                <br>
                                ${attr.description || 'Sin descripción'}
                                <br>
                                (${attr.x1}, ${attr.y1}) → (${attr.x2}, ${attr.y2})
                            </small>
                        </div>
                        <div class="btn-group-vertical btn-group-sm">
                            <button class="btn btn-sm btn-outline-primary" onclick="editAttribute(${index})" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeAttribute(${index})" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;

    // Enable save button if there are new attributes
    const hasNewAttributes = configuredAttributes.some(a => a._isNew);
    document.getElementById('saveAllBtn').disabled = !hasNewAttributes;

    redrawCanvas();
}

// Edit attribute
function editAttribute(index) {
    const attr = configuredAttributes[index];

    // Set editing index
    editingAttributeIndex = index;

    // Fill form with attribute data
    document.getElementById('attrNameDef').value = attr.label;
    document.getElementById('attrDescriptionDef').value = attr.description || '';
    document.getElementById('attrDataType').value = attr.data_type || 'text';

    // Set current box to attribute coordinates
    currentAttributeBox = {
        x1: attr.x1,
        y1: attr.y1,
        x2: attr.x2,
        y2: attr.y2
    };

    // Update coordinates display
    document.getElementById('attrCoordinates').innerHTML = `
        <span class="badge bg-success">
            (${currentAttributeBox.x1}, ${currentAttributeBox.y1}) → (${currentAttributeBox.x2}, ${currentAttributeBox.y2})
        </span>
    `;

    // Change button text
    const saveBtn = document.querySelector('button[onclick="saveAttribute()"]');
    saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Actualizar Atributo';
    saveBtn.classList.remove('btn-primary');
    saveBtn.classList.add('btn-warning');

    // Add cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'btn btn-secondary';
    cancelBtn.innerHTML = '<i class="bi bi-x-circle"></i> Cancelar';
    cancelBtn.onclick = cancelEditAttribute;
    saveBtn.parentElement.appendChild(cancelBtn);

    // Scroll to form
    document.getElementById('attrNameDef').scrollIntoView({ behavior: 'smooth' });

    // Redraw canvas to highlight the attribute being edited
    redrawCanvas();

    showToast('Editando atributo. Modifica los valores y presiona "Actualizar"', 'info');
}

// Cancel edit attribute
function cancelEditAttribute() {
    editingAttributeIndex = null;
    currentAttributeBox = null;

    // Reset form
    document.getElementById('attributeDefinitionForm').reset();
    document.getElementById('attrCoordinates').innerHTML = 'Dibuja un rectángulo en la imagen';

    // Reset button
    const saveBtn = document.querySelector('button[onclick="saveAttribute()"]');
    saveBtn.innerHTML = '<i class="bi bi-plus-circle"></i> Agregar Atributo';
    saveBtn.classList.remove('btn-warning');
    saveBtn.classList.add('btn-primary');

    // Remove cancel button
    const cancelBtn = saveBtn.parentElement.querySelector('.btn-secondary');
    if (cancelBtn) cancelBtn.remove();

    redrawCanvas();
}

// Remove attribute from list
function removeAttribute(index) {
    const attr = configuredAttributes[index];

    if (attr._isNew) {
        // Just remove from local list
        if (confirm('¿Eliminar este atributo de la lista?')) {
            configuredAttributes.splice(index, 1);
            displayConfiguredAttributes();
        }
    } else {
        // Delete from database
        if (confirm('¿Eliminar este atributo de la base de datos? Esta acción no se puede deshacer.')) {
            DocumentAPI.deleteCoordinate(attr.id).then(() => {
                configuredAttributes.splice(index, 1);
                displayConfiguredAttributes();
                showToast('Atributo eliminado', 'success');
            }).catch(error => {
                showToast('Error al eliminar: ' + error.message, 'error');
            });
        }
    }
}

// Save all new attributes to database
async function saveAllAttributes() {
    const newAttributes = configuredAttributes.filter(attr => attr._isNew);
    console.log('Saving new attributes:', newAttributes);
    if (newAttributes.length === 0) {
        showToast('No hay atributos nuevos para guardar', 'info');
        return;
    }

    try {
        for (const attr of newAttributes) {
            console.log('Processing attribute:', attr);

            // First, create the configurable attribute if needed
            const attributes = await DocumentAPI.listAttributes();
            console.log('Existing attributes:', attributes);

            let attribute = attributes.find(a => a.attribute_name === attr.label);

            if (!attribute) {
                console.log('Creating new attribute:', {
                    attribute_name: attr.label,
                    attribute_key: attr.label.toLowerCase().replace(/\s+/g, '_'),
                    description: attr.description || '',
                    is_required: 0,
                    validation_rules: {
                        type: attr.data_type || 'text'
                    }
                });

                // Create new attribute
                attribute = await DocumentAPI.createAttribute({
                    attribute_name: attr.label,
                    attribute_key: attr.label.toLowerCase().replace(/\s+/g, '_'),
                    description: attr.description || '',
                    is_required: 0,
                    validation_rules: {
                        type: attr.data_type || 'text'
                    }
                });

                console.log('Attribute created:', attribute);
            } else {
                console.log('Found existing attribute:', attribute);
            }

            // Create the coordinate
            const coordinateData = {
                page_type_id: attr.page_type_id,
                attribute_id: attribute.id,
                label: attr.label,
                description: attr.description || null,
                data_type: attr.data_type || 'text',
                x1: Math.round(attr.x1),
                y1: Math.round(attr.y1),
                x2: Math.round(attr.x2),
                y2: Math.round(attr.y2)
            };

            console.log('Creating coordinate:', coordinateData);
            await DocumentAPI.createCoordinate(coordinateData);

            // Mark as saved
            attr._isNew = false;
            attr.id = attribute.id;
        }

        showToast('Todos los atributos guardados exitosamente', 'success');
        document.getElementById('saveAllBtn').disabled = true;
        displayConfiguredAttributes();

    } catch (error) {
        console.error('Error completo:', error);
        console.error('Error stack:', error.stack);
        showToast('Error al guardar atributos: ' + error.message, 'error');
    }
}

// Auto-load attribute configuration when on standalone page
document.addEventListener('DOMContentLoaded', function() {
    const attributeConfigContent = document.getElementById('attribute-config-content');
    if (attributeConfigContent) {
        // Show immediately on standalone page
        showAttributeConfiguration();
    }
});
