// Prompts Management Module

class PromptsManager {
    constructor() {
        this.currentPromptId = null;
        this.promptModal = null;
        this.promptDetailModal = null;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Initialize modals
        this.promptModal = new bootstrap.Modal(document.getElementById('promptModal'));
        this.promptDetailModal = new bootstrap.Modal(document.getElementById('promptDetailModal'));

        // Tab activation - load prompts when tab is shown
        const promptsTab = document.getElementById('prompts-tab');
        if (promptsTab) {
            promptsTab.addEventListener('shown.bs.tab', () => {
                this.loadPrompts();
            });
        }

        // Filters
        const typeFilter = document.getElementById('promptTypeFilter');
        const activeOnlyFilter = document.getElementById('activeOnlyFilter');

        if (typeFilter) {
            typeFilter.addEventListener('change', () => this.loadPrompts());
        }
        if (activeOnlyFilter) {
            activeOnlyFilter.addEventListener('change', () => this.loadPrompts());
        }

        // Buttons
        const createPromptBtn = document.getElementById('createPromptBtn');
        const savePromptBtn = document.getElementById('savePromptBtn');
        const initDefaultPromptsBtn = document.getElementById('initDefaultPromptsBtn');

        if (createPromptBtn) {
            createPromptBtn.addEventListener('click', () => this.openCreateModal());
        }
        if (savePromptBtn) {
            savePromptBtn.addEventListener('click', () => this.savePrompt());
        }
        if (initDefaultPromptsBtn) {
            initDefaultPromptsBtn.addEventListener('click', () => this.initializeDefaults());
        }

        // Form validation
        const promptType = document.getElementById('promptType');
        if (promptType) {
            promptType.addEventListener('change', () => this.updateDocumentTypeField());
        }
    }

    async loadPrompts() {
        const typeFilter = document.getElementById('promptTypeFilter');
        const activeOnlyFilter = document.getElementById('activeOnlyFilter');
        const promptsList = document.getElementById('promptsList');

        if (!promptsList) return;

        try {
            promptsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p class="mt-2">Cargando prompts...</p></div>';

            const promptType = typeFilter ? typeFilter.value : null;
            const activeOnly = activeOnlyFilter ? activeOnlyFilter.checked : false;

            const prompts = await DocumentAPI.listPrompts(promptType, activeOnly);

            if (prompts.length === 0) {
                promptsList.innerHTML = `
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i> No hay prompts configurados.
                        <button type="button" class="btn btn-sm btn-primary ms-2" onclick="promptsManager.initializeDefaults()">
                            Inicializar Defaults
                        </button>
                    </div>
                `;
                return;
            }

            promptsList.innerHTML = this.renderPromptsList(prompts);
        } catch (error) {
            console.error('Error loading prompts:', error);
            promptsList.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> Error cargando prompts: ${error.message}
                </div>
            `;
        }
    }

    renderPromptsList(prompts) {
        // Group prompts by type
        const classification = prompts.filter(p => p.prompt_type === 'classification');
        const extraction = prompts.filter(p => p.prompt_type === 'extraction');

        let html = '';

        // Classification prompts
        if (classification.length > 0) {
            html += `
                <h6 class="text-primary mt-3"><i class="bi bi-diagram-3"></i> Prompts de Clasificación</h6>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Descripción</th>
                                <th>Estado</th>
                                <th>Fecha</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${classification.map(p => this.renderPromptRow(p)).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Extraction prompts - group by document type
        if (extraction.length > 0) {
            const groupedByDocType = {};
            extraction.forEach(p => {
                const docType = p.document_type || 'Sin tipo';
                if (!groupedByDocType[docType]) {
                    groupedByDocType[docType] = [];
                }
                groupedByDocType[docType].push(p);
            });

            html += `<h6 class="text-success mt-4"><i class="bi bi-file-earmark-text"></i> Prompts de Extracción</h6>`;

            Object.keys(groupedByDocType).sort().forEach(docType => {
                html += `
                    <h6 class="text-muted mt-3 ms-3">${this.formatDocumentType(docType)}</h6>
                    <div class="table-responsive">
                        <table class="table table-hover table-sm">
                            <thead>
                                <tr>
                                    <th>Nombre</th>
                                    <th>Descripción</th>
                                    <th>Estado</th>
                                    <th>Fecha</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${groupedByDocType[docType].map(p => this.renderPromptRow(p)).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            });
        }

        return html;
    }

    renderPromptRow(prompt) {
        const isActive = prompt.is_active === 1;
        const statusBadge = isActive
            ? '<span class="badge bg-success">Activo</span>'
            : '<span class="badge bg-secondary">Inactivo</span>';

        const date = new Date(prompt.created_at).toLocaleDateString('es-AR');

        const description = prompt.description
            ? (prompt.description.length > 50 ? prompt.description.substring(0, 50) + '...' : prompt.description)
            : '<span class="text-muted">Sin descripción</span>';

        return `
            <tr>
                <td><strong>${prompt.name}</strong></td>
                <td>${description}</td>
                <td>${statusBadge}</td>
                <td>${date}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-info" onclick="promptsManager.viewPrompt(${prompt.id})" title="Ver">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-primary" onclick="promptsManager.editPrompt(${prompt.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-${isActive ? 'warning' : 'success'}"
                                onclick="promptsManager.toggleActive(${prompt.id}, ${isActive ? 0 : 1})"
                                title="${isActive ? 'Desactivar' : 'Activar'}">
                            <i class="bi bi-${isActive ? 'toggle-on' : 'toggle-off'}"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="promptsManager.deletePrompt(${prompt.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    formatDocumentType(docType) {
        const types = {
            'factura': 'Factura',
            'orden_compra': 'Orden de Compra',
            'certificado_origen': 'Certificado de Origen',
            'especificacion_tecnica': 'Especificación Técnica',
            'contrato': 'Contrato',
            'remito': 'Remito'
        };
        return types[docType] || docType;
    }

    openCreateModal() {
        this.currentPromptId = null;
        document.getElementById('promptModalLabel').textContent = 'Nuevo Prompt';
        document.getElementById('promptForm').reset();
        document.getElementById('promptId').value = '';
        this.updateDocumentTypeField();
        this.promptModal.show();
    }

    async editPrompt(id) {
        try {
            const prompt = await DocumentAPI.getPrompt(id);
            this.currentPromptId = id;

            document.getElementById('promptModalLabel').textContent = 'Editar Prompt';
            document.getElementById('promptId').value = prompt.id;
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptType').value = prompt.prompt_type;
            document.getElementById('promptDocumentType').value = prompt.document_type || '';
            document.getElementById('promptTemplate').value = prompt.prompt_template;
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptIsActive').checked = prompt.is_active === 1;

            this.updateDocumentTypeField();
            this.promptModal.show();
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.showAlert('danger', `Error cargando prompt: ${error.message}`);
        }
    }

    async viewPrompt(id) {
        try {
            const prompt = await DocumentAPI.getPrompt(id);
            const content = document.getElementById('promptDetailContent');

            const statusBadge = prompt.is_active === 1
                ? '<span class="badge bg-success">Activo</span>'
                : '<span class="badge bg-secondary">Inactivo</span>';

            const typeBadge = prompt.prompt_type === 'classification'
                ? '<span class="badge bg-primary">Clasificación</span>'
                : '<span class="badge bg-success">Extracción</span>';

            let docTypeInfo = '';
            if (prompt.document_type) {
                docTypeInfo = `
                    <div class="mb-3">
                        <strong>Tipo de Documento:</strong>
                        <span class="badge bg-info">${this.formatDocumentType(prompt.document_type)}</span>
                    </div>
                `;
            }

            content.innerHTML = `
                <div class="mb-3">
                    <h5>${prompt.name}</h5>
                    ${statusBadge} ${typeBadge}
                </div>

                ${docTypeInfo}

                <div class="mb-3">
                    <strong>Descripción:</strong>
                    <p>${prompt.description || '<em class="text-muted">Sin descripción</em>'}</p>
                </div>

                <div class="mb-3">
                    <strong>Template del Prompt:</strong>
                    <pre class="bg-light p-3 rounded"><code>${this.escapeHtml(prompt.prompt_template)}</code></pre>
                </div>

                <div class="mb-3">
                    <strong>Variables:</strong>
                    <div class="mt-2">
                        ${this.renderVariables(prompt.variables)}
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <strong>Creado:</strong> ${new Date(prompt.created_at).toLocaleString('es-AR')}
                    </div>
                    <div class="col-md-6">
                        <strong>Actualizado:</strong> ${prompt.updated_at ? new Date(prompt.updated_at).toLocaleString('es-AR') : 'N/A'}
                    </div>
                </div>
            `;

            document.getElementById('promptDetailModalLabel').textContent = `Prompt: ${prompt.name}`;
            this.promptDetailModal.show();
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.showAlert('danger', `Error cargando prompt: ${error.message}`);
        }
    }

    renderVariables(variables) {
        if (!variables || Object.keys(variables).length === 0) {
            return '<em class="text-muted">No hay variables definidas</em>';
        }

        return `
            <ul class="list-unstyled">
                ${Object.entries(variables).map(([key, value]) => `
                    <li><code>{${key}}</code> - ${value}</li>
                `).join('')}
            </ul>
        `;
    }

    async savePrompt() {
        const form = document.getElementById('promptForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const promptData = {
            name: document.getElementById('promptName').value.trim(),
            prompt_type: document.getElementById('promptType').value,
            document_type: document.getElementById('promptDocumentType').value || null,
            prompt_template: document.getElementById('promptTemplate').value,
            description: document.getElementById('promptDescription').value.trim() || null,
            is_active: document.getElementById('promptIsActive').checked ? 1 : 0,
            variables: this.extractVariables()
        };

        // Validate extraction prompts have document_type
        if (promptData.prompt_type === 'extraction' && !promptData.document_type) {
            this.showAlert('warning', 'Los prompts de extracción requieren especificar un tipo de documento');
            return;
        }

        // Validate classification prompts don't have document_type
        if (promptData.prompt_type === 'classification' && promptData.document_type) {
            promptData.document_type = null;
        }

        try {
            const saveBtn = document.getElementById('savePromptBtn');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

            if (this.currentPromptId) {
                await DocumentAPI.updatePrompt(this.currentPromptId, promptData);
                this.showAlert('success', 'Prompt actualizado exitosamente');
            } else {
                await DocumentAPI.createPrompt(promptData);
                this.showAlert('success', 'Prompt creado exitosamente');
            }

            this.promptModal.hide();
            this.loadPrompts();
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.showAlert('danger', `Error guardando prompt: ${error.message}`);
        } finally {
            const saveBtn = document.getElementById('savePromptBtn');
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Guardar';
        }
    }

    extractVariables() {
        const template = document.getElementById('promptTemplate').value;
        const variables = {};

        // Extract variables from template
        const matches = template.match(/\{(\w+)\}/g);
        if (matches) {
            matches.forEach(match => {
                const varName = match.slice(1, -1); // Remove { and }
                if (varName === 'text_content') {
                    variables[varName] = 'Contenido de texto del documento';
                } else if (varName === 'document_type') {
                    variables[varName] = 'Tipo de documento';
                } else {
                    variables[varName] = 'Variable personalizada';
                }
            });
        }

        return variables;
    }

    async toggleActive(id, newStatus) {
        try {
            await DocumentAPI.updatePrompt(id, { is_active: newStatus });
            this.showAlert('success', `Prompt ${newStatus === 1 ? 'activado' : 'desactivado'} exitosamente`);
            this.loadPrompts();
        } catch (error) {
            console.error('Error toggling prompt:', error);
            this.showAlert('danger', `Error: ${error.message}`);
        }
    }

    async deletePrompt(id) {
        if (!confirm('¿Está seguro de eliminar este prompt? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            await DocumentAPI.deletePrompt(id);
            this.showAlert('success', 'Prompt eliminado exitosamente');
            this.loadPrompts();
        } catch (error) {
            console.error('Error deleting prompt:', error);
            this.showAlert('danger', `Error eliminando prompt: ${error.message}`);
        }
    }

    async initializeDefaults() {
        if (!confirm('¿Desea inicializar los prompts por defecto? Esto solo funcionará si no hay prompts en la base de datos.')) {
            return;
        }

        try {
            const btn = document.getElementById('initDefaultPromptsBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Inicializando...';

            await DocumentAPI.initializeDefaultPrompts();
            this.showAlert('success', 'Prompts por defecto inicializados exitosamente');
            this.loadPrompts();
        } catch (error) {
            console.error('Error initializing defaults:', error);
            this.showAlert('danger', `Error: ${error.message}`);
        } finally {
            const btn = document.getElementById('initDefaultPromptsBtn');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-download"></i> Inicializar Defaults';
        }
    }

    updateDocumentTypeField() {
        const promptType = document.getElementById('promptType').value;
        const documentTypeField = document.getElementById('promptDocumentType');

        if (promptType === 'classification') {
            documentTypeField.value = '';
            documentTypeField.disabled = true;
            documentTypeField.required = false;
        } else if (promptType === 'extraction') {
            documentTypeField.disabled = false;
            documentTypeField.required = true;
        } else {
            documentTypeField.disabled = true;
            documentTypeField.required = false;
        }
    }

    showAlert(type, message) {
        // Create alert at the top of the prompts tab
        const promptsTab = document.getElementById('prompts');
        if (!promptsTab) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        promptsTab.insertBefore(alertDiv, promptsTab.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the prompts manager
const promptsManager = new PromptsManager();
