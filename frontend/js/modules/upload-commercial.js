// Commercial Documents Upload Page

// Toast Notification Function
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = `toast-${Date.now()}`;

    const bgClass = type === 'success' ? 'bg-success' :
                    type === 'error' ? 'bg-danger' :
                    type === 'warning' ? 'bg-warning' : 'bg-info';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    toastElement.addEventListener('hidden.bs.toast', function() { this.remove(); });
}

document.addEventListener('DOMContentLoaded', () => {
    setupCommercialUpload();
    loadCommercialDocuments();
});

function setupCommercialUpload() {
    const form = document.getElementById('commercialUploadForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fileInput = document.getElementById('commercialFile');
        const reference = document.getElementById('commercialReference').value;
        const progressDiv = document.getElementById('commercialUploadProgress');
        const resultDiv = document.getElementById('commercialUploadResult');

        if (!fileInput.files.length) {
            showToast('Selecciona un archivo', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        if (reference) formData.append('reference', reference);

        progressDiv.style.display = 'block';
        resultDiv.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}/documents/upload/commercial`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showToast('Documento subido exitosamente', 'success');
                form.reset();
                loadCommercialDocuments();

                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Documento procesado:</strong><br>
                        Tipo: ${data.document_type || 'N/A'}<br>
                        ID: ${data.document_id}
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Error al subir documento');
            }
        } catch (error) {
            console.error('Error:', error);
            showToast(error.message, 'error');
            resultDiv.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        } finally {
            progressDiv.style.display = 'none';
        }
    });
}

async function loadCommercialDocuments() {
    const listContainer = document.getElementById('commercialDocumentsList');

    try {
        const response = await fetch(`${API_BASE_URL}/documents/commercial`);
        const documents = await response.json();

        if (documents.length === 0) {
            listContainer.innerHTML = '<p class="text-muted">No hay documentos subidos</p>';
            return;
        }

        const docsHtml = documents.map(doc => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h6 class="mb-1">${doc.filename}</h6>
                            <small class="text-muted">
                                Tipo: ${doc.document_type || 'N/A'} |
                                Referencia: ${doc.reference || 'Sin referencia'} |
                                Subido: ${new Date(doc.uploaded_at).toLocaleString('es-AR')}
                            </small>
                        </div>
                        <div class="col-md-4 text-end">
                            <button class="btn btn-sm btn-info" onclick="viewDocument(${doc.id}, 'commercial')">
                                <i class="bi bi-eye"></i> Ver
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteDocument(${doc.id}, 'commercial')">
                                <i class="bi bi-trash"></i> Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        listContainer.innerHTML = docsHtml;
    } catch (error) {
        console.error('Error loading documents:', error);
        listContainer.innerHTML = '<p class="text-danger">Error al cargar documentos</p>';
    }
}

async function viewDocument(id, type) {
    try {
        const response = await fetch(`${API_BASE_URL}/documents/${type}/${id}`);
        const doc = await response.json();
        alert(`Documento: ${doc.filename}\nTipo: ${doc.document_type}\nDatos extraídos: ${JSON.stringify(doc.extracted_data, null, 2)}`);
    } catch (error) {
        showToast('Error al ver documento', 'error');
    }
}

async function deleteDocument(id, type) {
    if (!confirm('¿Estás seguro de eliminar este documento?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${type}/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Documento eliminado', 'success');
            loadCommercialDocuments();
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}
