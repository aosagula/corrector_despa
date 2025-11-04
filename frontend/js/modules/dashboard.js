// Dashboard page logic

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardStats();
    await loadRecentActivity();
});

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        // Load commercial documents count
        const commercialDocs = await fetch(`${API_BASE_URL}/documents/commercial`).then(r => r.json());
        document.getElementById('stat-commercial-docs').textContent = commercialDocs.length || 0;

        // Load provisional documents count
        const provisionalDocs = await fetch(`${API_BASE_URL}/documents/provisional`).then(r => r.json());
        document.getElementById('stat-provisional-docs').textContent = provisionalDocs.length || 0;

        // Load comparisons count (from history)
        const history = await fetch(`${API_BASE_URL}/comparisons/history`).then(r => r.json());
        document.getElementById('stat-comparisons').textContent = history.length || 0;

        // Load active prompts count
        const prompts = await fetch(`${API_BASE_URL}/prompts`).then(r => r.json());
        const activePrompts = prompts.filter(p => p.is_active);
        document.getElementById('stat-prompts').textContent = activePrompts.length || 0;

    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Load recent activity
async function loadRecentActivity() {
    const activityContainer = document.getElementById('recent-activity');

    try {
        const history = await fetch(`${API_BASE_URL}/comparisons/history?limit=5`).then(r => r.json());

        if (history.length === 0) {
            activityContainer.innerHTML = '<p class="text-muted">No hay actividad reciente</p>';
            return;
        }

        const activityHtml = history.map(item => {
            const date = new Date(item.created_at).toLocaleString('es-AR');
            const statusBadge = item.status === 'completed'
                ? '<span class="badge bg-success">Completado</span>'
                : '<span class="badge bg-warning">Pendiente</span>';

            return `
                <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                    <div>
                        <strong>${item.commercial_filename || 'Documento'}</strong> vs
                        <strong>${item.provisional_filename || 'Provisorio'}</strong>
                        <br>
                        <small class="text-muted">${date}</small>
                    </div>
                    <div>
                        ${statusBadge}
                        <a href="/pages/history.html?id=${item.id}" class="btn btn-sm btn-outline-primary ms-2">
                            <i class="bi bi-eye"></i> Ver
                        </a>
                    </div>
                </div>
            `;
        }).join('');

        activityContainer.innerHTML = activityHtml;

    } catch (error) {
        console.error('Error loading recent activity:', error);
        activityContainer.innerHTML = '<p class="text-danger">Error al cargar la actividad reciente</p>';
    }
}
