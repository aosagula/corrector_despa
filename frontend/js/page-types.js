// Page Types Management

// Load page types when page is ready or tab is shown
document.addEventListener('DOMContentLoaded', function() {
    const pageTypesTab = document.getElementById('page-types-tab');

    if (pageTypesTab) {
        // Tab-based interface
        pageTypesTab.addEventListener('shown.bs.tab', function () {
            loadPageTypes();
        });
    }

    // If page types list exists on page load, load immediately (standalone page)
    const pageTypesList = document.getElementById('pageTypesList');
    if (pageTypesList) {
        loadPageTypes();
    }
});

// Load all page types
async function loadPageTypes() {
    try {
        const pageTypes = await DocumentAPI.listPageTypes();
        displayPageTypes(pageTypes);
    } catch (error) {
        console.error('Error loading page types:', error);
        document.getElementById('pageTypesList').innerHTML = `
            <div class="alert alert-danger">
                Error cargando tipos de páginas: ${error.message}
            </div>
        `;
    }
}

// Display page types in the UI
function displayPageTypes(pageTypes) {
    const container = document.getElementById('pageTypesList');

    if (pageTypes.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay tipos de páginas configurados.</p>';
        return;
    }

    const html = pageTypes.map(pt => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h5 class="card-title">
                            <span class="badge" style="background-color: ${pt.color}">&nbsp;&nbsp;&nbsp;</span>
                            ${pt.display_name}
                            <small class="text-muted">(${pt.name})</small>
                        </h5>
                        <p class="card-text">${pt.description || 'Sin descripción'}</p>
                        <button class="btn btn-sm btn-info" onclick="viewDetectionRules(${pt.id}, '${pt.display_name}')">
                            <i class="bi bi-rulers"></i> Ver Reglas (${pt.rules_count || 0})
                        </button>
                    </div>
                    <div class="btn-group-vertical btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editPageType(${pt.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deletePageType(${pt.id}, '${pt.display_name}')" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Show create page type modal
function showCreatePageTypeModal() {
    const modalHtml = `
        <div class="modal fade" id="pageTypeModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Nuevo Tipo de Página</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="pageTypeForm">
                            <div class="mb-3">
                                <label for="ptName" class="form-label">Nombre (identificador)*</label>
                                <input type="text" class="form-control" id="ptName" required
                                       pattern="[a-z_]+" title="Solo letras minúsculas y guiones bajos"
                                       placeholder="ej: caratula, items">
                                <small class="text-muted">Solo letras minúsculas y guiones bajos</small>
                            </div>
                            <div class="mb-3">
                                <label for="ptDisplayName" class="form-label">Nombre para mostrar*</label>
                                <input type="text" class="form-control" id="ptDisplayName" required
                                       placeholder="ej: Carátula, Items">
                            </div>
                            <div class="mb-3">
                                <label for="ptDescription" class="form-label">Descripción</label>
                                <textarea class="form-control" id="ptDescription" rows="2"
                                          placeholder="Descripción del tipo de página"></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="ptColor" class="form-label">Color</label>
                                <input type="color" class="form-control" id="ptColor" value="#007bff">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="savePageType()">Guardar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal
    const existingModal = document.getElementById('pageTypeModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('pageTypeModal'));
    modal.show();

    // Clean up on close
    document.getElementById('pageTypeModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// Save page type
async function savePageType() {
    const form = document.getElementById('pageTypeForm');

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const pageTypeData = {
        name: document.getElementById('ptName').value,
        display_name: document.getElementById('ptDisplayName').value,
        description: document.getElementById('ptDescription').value || null,
        color: document.getElementById('ptColor').value
    };

    try {
        await DocumentAPI.createPageType(pageTypeData);
        showToast('Tipo de página creado exitosamente', 'success');

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('pageTypeModal'));
        modal.hide();

        // Reload list
        loadPageTypes();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al crear tipo de página: ' + error.message, 'error');
    }
}

// Edit page type
async function editPageType(pageTypeId) {
    try {
        const pageType = await DocumentAPI.getPageType(pageTypeId);

        const modalHtml = `
            <div class="modal fade" id="editPageTypeModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Editar Tipo de Página</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editPageTypeForm">
                                <div class="mb-3">
                                    <label class="form-label">Nombre (identificador)</label>
                                    <input type="text" class="form-control" value="${pageType.name}" disabled>
                                </div>
                                <div class="mb-3">
                                    <label for="editPtDisplayName" class="form-label">Nombre para mostrar*</label>
                                    <input type="text" class="form-control" id="editPtDisplayName" required
                                           value="${pageType.display_name}">
                                </div>
                                <div class="mb-3">
                                    <label for="editPtDescription" class="form-label">Descripción</label>
                                    <textarea class="form-control" id="editPtDescription" rows="2">${pageType.description || ''}</textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="editPtColor" class="form-label">Color</label>
                                    <input type="color" class="form-control" id="editPtColor" value="${pageType.color}">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="updatePageType(${pageTypeId})">Actualizar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const existingModal = document.getElementById('editPageTypeModal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('editPageTypeModal'));
        modal.show();

        document.getElementById('editPageTypeModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar tipo de página: ' + error.message, 'error');
    }
}

// Update page type
async function updatePageType(pageTypeId) {
    const form = document.getElementById('editPageTypeForm');

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const updateData = {
        display_name: document.getElementById('editPtDisplayName').value,
        description: document.getElementById('editPtDescription').value || null,
        color: document.getElementById('editPtColor').value
    };

    try {
        await DocumentAPI.updatePageType(pageTypeId, updateData);
        showToast('Tipo de página actualizado exitosamente', 'success');

        const modal = bootstrap.Modal.getInstance(document.getElementById('editPageTypeModal'));
        modal.hide();

        loadPageTypes();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al actualizar tipo de página: ' + error.message, 'error');
    }
}

// Delete page type
async function deletePageType(pageTypeId, displayName) {
    if (!confirm(`¿Está seguro de eliminar el tipo de página "${displayName}"?\n\nEsto eliminará también todas las reglas de detección asociadas.`)) {
        return;
    }

    try {
        await DocumentAPI.deletePageType(pageTypeId);
        showToast('Tipo de página eliminado exitosamente', 'success');
        loadPageTypes();
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al eliminar tipo de página: ' + error.message, 'error');
    }
}

// Note: viewDetectionRules is now implemented in detection-rules.js
