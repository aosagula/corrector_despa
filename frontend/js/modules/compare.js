// Compare Documents Page
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = `toast-${Date.now()}`;
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
    const toastHtml = `<div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert"><div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toast = new bootstrap.Toast(document.getElementById(toastId), { autohide: true, delay: 5000 });
    toast.show();
}

document.addEventListener('DOMContentLoaded', () => {
    populateComparisonSelects();
    setupComparison();
});

async function populateComparisonSelects() {
    try {
        const [commercial, provisional] = await Promise.all([
            fetch(`${API_BASE_URL}/documents/commercial`).then(r => r.json()),
            fetch(`${API_BASE_URL}/documents/provisional`).then(r => r.json())
        ]);

        const commercialSelect = document.getElementById('selectCommercial');
        const provisionalSelect = document.getElementById('selectProvisional');

        commercialSelect.innerHTML = '<option value="">Seleccionar...</option>' +
            commercial.map(d => `<option value="${d.id}">${d.filename} (${d.reference || 'Sin ref'})</option>`).join('');

        provisionalSelect.innerHTML = '<option value="">Seleccionar...</option>' +
            provisional.map(d => `<option value="${d.id}">${d.filename} (${d.reference || 'Sin ref'})</option>`).join('');
    } catch (error) {
        showToast('Error al cargar documentos', 'error');
    }
}

function setupComparison() {
    document.getElementById('compareForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const commercialId = document.getElementById('selectCommercial').value;
        const provisionalId = document.getElementById('selectProvisional').value;

        if (!commercialId || !provisionalId) {
            showToast('Selecciona ambos documentos', 'error');
            return;
        }

        await performComparison(commercialId, provisionalId);
    });

    document.getElementById('batchCompareBtn').addEventListener('click', async () => {
        const provisionalId = document.getElementById('selectProvisional').value;
        if (!provisionalId) {
            showToast('Selecciona un documento provisorio', 'error');
            return;
        }

        const response = await fetch(`${API_BASE_URL}/documents/commercial`);
        const commercialDocs = await response.json();

        for (const doc of commercialDocs) {
            await performComparison(doc.id, provisionalId);
        }
    });
}

async function performComparison(commercialId, provisionalId) {
    const progressDiv = document.getElementById('compareProgress');
    const resultsDiv = document.getElementById('comparisonResults');

    progressDiv.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE_URL}/comparisons/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                commercial_id: parseInt(commercialId),
                provisional_id: parseInt(provisionalId)
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Comparación completada', 'success');
            displayComparisonResult(data);
        } else {
            throw new Error(data.error || 'Error en comparación');
        }
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        progressDiv.style.display = 'none';
    }
}

function displayComparisonResult(result) {
    const resultsDiv = document.getElementById('comparisonResults');
    const html = `
        <div class="card mb-3">
            <div class="card-header bg-${result.is_match ? 'success' : 'danger'} text-white">
                <h5><i class="bi bi-${result.is_match ? 'check-circle' : 'x-circle'}"></i>
                ${result.is_match ? 'Coincidencia' : 'No coincide'}</h5>
            </div>
            <div class="card-body">
                <h6>Diferencias:</h6>
                <pre>${JSON.stringify(result.differences, null, 2)}</pre>
            </div>
        </div>
    `;
    resultsDiv.innerHTML = html + resultsDiv.innerHTML;
}
