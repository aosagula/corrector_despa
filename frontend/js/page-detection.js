// Page Type Detection Viewer
let currentDetectionDocument = null;
let currentDetectionData = null;
let currentDetectionPage = 0;
let detectionCanvas = null;
let detectionCtx = null;
let detectionImage = null;
let detectionZoom = 0.4; // Default zoom 40%

// Show page detection viewer
async function showPageDetectionViewer() {
    const container = document.getElementById('page-detection-content');
    if (!container) {
        console.error('Container page-detection-content not found');
        return;
    }

    try {
        // Get list of provisional documents
        const documents = await DocumentAPI.listProvisionalDocuments();

        if (documents.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> No hay documentos provisorios disponibles.
                    <br>
                    <a href="../pages/upload-provisional.html" class="btn btn-sm btn-primary mt-2">
                        <i class="bi bi-upload"></i> Subir Documento Provisorio
                    </a>
                </div>
            `;
            return;
        }

        const docOptions = documents.map(doc =>
            `<option value="${doc.id}">${doc.filename}</option>`
        ).join('');

        const contentHtml = `
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label">Seleccionar Documento:</label>
                                    <select class="form-select" id="detectionDocumentSelect" onchange="loadDetectionDocument()">
                                        <option value="">Seleccionar documento...</option>
                                        ${docOptions}
                                    </select>
                                </div>
                                <div class="col-md-6" id="detectionInfo" style="display: none;">
                                    <div class="alert alert-info mb-0">
                                        <strong id="detectionFileName"></strong>
                                        <br>
                                        <small id="detectionStats"></small>
                                    </div>
                                </div>
                            </div>

                            <div id="detectionContent" style="display: none;">
                                <div class="row">
                                    <div class="col-md-9">
                                        <div class="card">
                                            <div class="card-header d-flex justify-content-between align-items-center">
                                                <div>
                                                    <span class="badge" id="currentPageTypeBadge" style="font-size: 1em;">
                                                        Página <span id="currentDetectionPageNum">1</span>
                                                    </span>
                                                    <span id="currentPageTypeLabel" class="ms-2"></span>
                                                </div>
                                                <div class="btn-group" role="group">
                                                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="changeDetectionZoom(-0.1)">
                                                        <i class="bi bi-zoom-out"></i> -
                                                    </button>
                                                    <button type="button" class="btn btn-sm btn-outline-secondary" id="detectionZoomBtn">
                                                        40%
                                                    </button>
                                                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="changeDetectionZoom(0.1)">
                                                        <i class="bi bi-zoom-in"></i> +
                                                    </button>
                                                </div>
                                            </div>
                                            <div class="card-body p-0">
                                                <div class="border" style="overflow: auto; max-height: 70vh; background: #f5f5f5;">
                                                    <canvas id="detectionCanvas" style="display: block;"></canvas>
                                                </div>
                                            </div>
                                            <div class="card-footer">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <button class="btn btn-secondary" onclick="navigateDetectionPage(-1)" id="prevDetectionBtn">
                                                        <i class="bi bi-chevron-left"></i> Anterior
                                                    </button>
                                                    <span id="detectionPageInfo">Página 1 de 1</span>
                                                    <button class="btn btn-secondary" onclick="navigateDetectionPage(1)" id="nextDetectionBtn">
                                                        Siguiente <i class="bi bi-chevron-right"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="col-md-3">
                                        <div class="card">
                                            <div class="card-header">
                                                <strong>Detecciones</strong>
                                            </div>
                                            <div class="card-body" id="detectionBoxesList" style="max-height: 70vh; overflow-y: auto;">
                                                <p class="text-muted">Selecciona una página</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="detectionLoading" style="display: none;" class="text-center py-5">
                                <div class="spinner-border" role="status">
                                    <span class="visually-hidden">Cargando...</span>
                                </div>
                                <p class="mt-3">Detectando tipos de página...</p>
                            </div>
                        </div>
        `;

        container.innerHTML = contentHtml;

        // Initialize canvas after DOM insertion
        detectionCanvas = document.getElementById('detectionCanvas');
        if (detectionCanvas) {
            detectionCtx = detectionCanvas.getContext('2d');
        }

    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i> Error al cargar el visor: ${error.message}
            </div>
        `;
    }
}

// Load detection for selected document
async function loadDetectionDocument() {
    const docId = document.getElementById('detectionDocumentSelect').value;
    if (!docId) {
        document.getElementById('detectionContent').style.display = 'none';
        document.getElementById('detectionInfo').style.display = 'none';
        return;
    }

    try {
        document.getElementById('detectionLoading').style.display = 'block';
        document.getElementById('detectionContent').style.display = 'none';

        const result = await DocumentAPI.detectProvisionalPages(parseInt(docId));

        currentDetectionDocument = parseInt(docId);
        currentDetectionData = result;
        currentDetectionPage = 0;
        detectionZoom = 0.4; // Reset to default 40% zoom

        // Show info
        document.getElementById('detectionFileName').textContent = result.filename;

        const stats = result.pages.reduce((acc, page) => {
            const type = page.page_type_display_name || 'No detectado';
            acc[type] = (acc[type] || 0) + 1;
            return acc;
        }, {});

        const statsText = Object.entries(stats)
            .map(([type, count]) => `${type}: ${count}`)
            .join(', ');

        document.getElementById('detectionStats').textContent = statsText;
        document.getElementById('detectionInfo').style.display = 'block';

        document.getElementById('detectionLoading').style.display = 'none';
        document.getElementById('detectionContent').style.display = 'block';

        // Load first page
        await displayDetectionPage();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('detectionLoading').style.display = 'none';
        showToast('Error al detectar páginas: ' + error.message, 'error');
    }
}

// Display current detection page
async function displayDetectionPage() {
    if (!currentDetectionData || !currentDetectionData.pages[currentDetectionPage]) {
        return;
    }

    const pageData = currentDetectionData.pages[currentDetectionPage];
    const pageNum = pageData.page_number;

    // Update UI
    document.getElementById('currentDetectionPageNum').textContent = pageNum;
    document.getElementById('detectionPageInfo').textContent =
        `Página ${currentDetectionPage + 1} de ${currentDetectionData.pages.length}`;

    // Update page type badge
    const badge = document.getElementById('currentPageTypeBadge');
    badge.style.backgroundColor = pageData.page_type_color;

    const label = document.getElementById('currentPageTypeLabel');
    label.innerHTML = `<strong>${pageData.page_type_display_name}</strong>`;
    if (pageData.confidence > 0) {
        label.innerHTML += ` <small class="text-muted">(${Math.round(pageData.confidence * 100)}%)</small>`;
    }

    // Update navigation buttons
    document.getElementById('prevDetectionBtn').disabled = currentDetectionPage === 0;
    document.getElementById('nextDetectionBtn').disabled =
        currentDetectionPage === currentDetectionData.pages.length - 1;

    // Load image
    const imageUrl = DocumentAPI.getProvisionalDocumentImageUrl(currentDetectionDocument, pageNum);

    const img = new Image();
    img.onload = function() {
        detectionImage = img;
        renderDetectionCanvas();
        displayDetectionBoxes(pageData.detection_boxes);
    };
    img.onerror = function() {
        showToast('Error al cargar imagen de página ' + pageNum, 'error');
    };
    img.src = imageUrl;
}

// Render canvas with detection boxes
function renderDetectionCanvas() {
    if (!detectionImage) return;

    // Set canvas size
    detectionCanvas.width = detectionImage.width * detectionZoom;
    detectionCanvas.height = detectionImage.height * detectionZoom;

    // Draw image
    detectionCtx.drawImage(detectionImage, 0, 0, detectionCanvas.width, detectionCanvas.height);

    // Draw detection boxes
    const pageData = currentDetectionData.pages[currentDetectionPage];
    if (pageData && pageData.detection_boxes) {
        pageData.detection_boxes.forEach((box, index) => {
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
            const color = colors[index % colors.length];

            detectionCtx.strokeStyle = color;
            detectionCtx.lineWidth = 3;
            detectionCtx.strokeRect(
                box.x1 * detectionZoom,
                box.y1 * detectionZoom,
                (box.x2 - box.x1) * detectionZoom,
                (box.y2 - box.y1) * detectionZoom
            );

            // Draw label
            detectionCtx.fillStyle = color;
            detectionCtx.fillRect(
                box.x1 * detectionZoom,
                (box.y1 - 20) * detectionZoom,
                150 * detectionZoom,
                20 * detectionZoom
            );
            detectionCtx.fillStyle = 'white';
            detectionCtx.font = `${12 * detectionZoom}px Arial`;
            detectionCtx.fillText(
                box.attribute_name,
                (box.x1 + 5) * detectionZoom,
                (box.y1 - 5) * detectionZoom
            );
        });
    }
}

// Display detection boxes in sidebar
function displayDetectionBoxes(boxes) {
    const container = document.getElementById('detectionBoxesList');

    if (!boxes || boxes.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay detecciones en esta página</p>';
        return;
    }

    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];

    // Map match types to Spanish labels
    const matchTypeLabels = {
        'contains': 'Contiene',
        'not_contains': 'No Contiene',
        'exact': 'Exacto',
        'not_exact': 'No Igual',
        'regex': 'Expresión Regular'
    };

    const html = boxes.map((box, index) => {
        const color = colors[index % colors.length];
        const matchLabel = matchTypeLabels[box.match_type] || box.match_type;
        return `
            <div class="card mb-2" style="border-left: 4px solid ${color};">
                <div class="card-body p-2">
                    <strong style="color: ${color};">${box.attribute_name}</strong>
                    <br>
                    <small class="text-muted">Tipo: <span class="badge bg-secondary">${matchLabel}</span></small>
                    <br>
                    <small class="text-muted">Valor de Referencia: ${box.expected_value || 'N/A'}</small>
                    <br>
                    <small class="text-success">Encontrado: ${box.found_value || 'N/A'}</small>
                    <br>
                    <small class="text-muted">
                        (${box.x1}, ${box.y1}) → (${box.x2}, ${box.y2})
                    </small>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

// Navigate between pages
function navigateDetectionPage(delta) {
    if (!currentDetectionData) return;

    currentDetectionPage += delta;

    if (currentDetectionPage < 0) {
        currentDetectionPage = 0;
    } else if (currentDetectionPage >= currentDetectionData.pages.length) {
        currentDetectionPage = currentDetectionData.pages.length - 1;
    }

    displayDetectionPage();
}

// Change zoom
function changeDetectionZoom(delta) {
    detectionZoom += delta;

    if (detectionZoom < 0.2) {
        detectionZoom = 0.2;
    } else if (detectionZoom > 10.0) {
        detectionZoom = 10.0;
    }

    document.getElementById('detectionZoomBtn').textContent = `${Math.round(detectionZoom * 100)}%`;
    renderDetectionCanvas();
}

// Auto-load page detection viewer when on standalone page
document.addEventListener('DOMContentLoaded', function() {
    const pageDetectionContent = document.getElementById('page-detection-content');
    if (pageDetectionContent) {
        // Show immediately on standalone page
        showPageDetectionViewer();
    }
});
