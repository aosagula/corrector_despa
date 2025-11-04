// History Page
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});

async function loadHistory() {
    const historyList = document.getElementById('historyList');

    try {
        const response = await fetch(`${API_BASE_URL}/comparisons/history`);
        const history = await response.json();

        if (history.length === 0) {
            historyList.innerHTML = '<p class="text-muted">No hay comparaciones en el historial</p>';
            return;
        }

        const historyHtml = history.map(item => {
            const date = new Date(item.created_at).toLocaleString('es-AR');
            const statusBadge = item.is_match
                ? '<span class="badge bg-success">Coincide</span>'
                : '<span class="badge bg-danger">No coincide</span>';

            return `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h6>${item.commercial_filename || 'Comercial'} vs ${item.provisional_filename || 'Provisorio'}</h6>
                                <small class="text-muted">${date}</small>
                            </div>
                            <div class="col-md-4 text-end">
                                ${statusBadge}
                                <button class="btn btn-sm btn-info ms-2" onclick="viewComparison(${item.id})">
                                    <i class="bi bi-eye"></i> Ver Detalles
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        historyList.innerHTML = historyHtml;
    } catch (error) {
        console.error('Error:', error);
        historyList.innerHTML = '<p class="text-danger">Error al cargar el historial</p>';
    }
}

async function viewComparison(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/comparisons/${id}`);
        const comparison = await response.json();
        alert(`Comparación #${id}\nCoincide: ${comparison.is_match ? 'Sí' : 'No'}\nDiferencias: ${JSON.stringify(comparison.differences, null, 2)}`);
    } catch (error) {
        alert('Error al cargar detalles de la comparación');
    }
}
