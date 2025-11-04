// Extract Attributes Module

let extractedData = null;
let currentProvisionalId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadProvisionalDocuments();
    setupEventListeners();
});

// Load provisional documents
async function loadProvisionalDocuments() {
    const select = document.getElementById('provisionalSelect');

    try {
        const response = await fetch(`${API_BASE_URL}/documents/provisional`);
        const documents = await response.json();

        if (documents.length === 0) {
            select.innerHTML = '<option value="">No hay documentos provisorios</option>';
            return;
        }

        select.innerHTML = '<option value="">Seleccionar documento...</option>' +
            documents.map(doc =>
                `<option value="${doc.id}">${doc.filename} ${doc.reference ? `(${doc.reference})` : ''}</option>`
            ).join('');

    } catch (error) {
        console.error('Error loading documents:', error);
        showToast('Error al cargar documentos provisorios', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('provisionalSelect').addEventListener('change', (e) => {
        const extractBtn = document.getElementById('extractBtn');
        extractBtn.disabled = !e.target.value;
        currentProvisionalId = e.target.value ? parseInt(e.target.value) : null;
    });

    document.getElementById('extractBtn').addEventListener('click', extractAttributes);
    document.getElementById('saveBtn').addEventListener('click', saveExtractedAttributes);
    document.getElementById('downloadJsonBtn').addEventListener('click', downloadJson);
}

// Extract attributes from provisional document
async function extractAttributes() {
    if (!currentProvisionalId) return;

    const progressDiv = document.getElementById('extractionProgress');
    const resultsDiv = document.getElementById('extractionResults');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');

    progressDiv.style.display = 'block';
    resultsDiv.style.display = 'none';
    extractedData = null;

    try {
        // Step 1: Detect page types
        progressBar.style.width = '10%';
        progressText.textContent = '10%';
        progressStatus.textContent = 'Detectando tipos de páginas...';

        const detectionResponse = await fetch(`${API_BASE_URL}/provisional-documents/${currentProvisionalId}/detect-pages`, {
            method: 'POST'
        });

        if (!detectionResponse.ok) {
            throw new Error('Error al detectar tipos de páginas');
        }

        const detectionData = await detectionResponse.json();
        const pages = detectionData.pages || [];

        progressBar.style.width = '30%';
        progressText.textContent = '30%';
        progressStatus.textContent = `${pages.length} páginas detectadas. Extrayendo atributos...`;

        // Step 2: Extract attributes for each page
        const extractedPages = [];
        const totalPages = pages.length;

        for (let i = 0; i < totalPages; i++) {
            const page = pages[i];
            const progress = 30 + ((i + 1) / totalPages * 60);
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
            progressStatus.textContent = `Extrayendo atributos de página ${i + 1} de ${totalPages} (${page.page_type_display_name})...`;

            // Extract attributes for this page
            const extractResponse = await fetch(`${API_BASE_URL}/provisional-documents/${currentProvisionalId}/extract-page-attributes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_number: page.page_number,
                    page_type_id: page.page_type_id
                })
            });

            if (extractResponse.ok) {
                const pageAttributes = await extractResponse.json();
                extractedPages.push({
                    page_number: page.page_number,
                    page_type: page.page_type_name,
                    page_type_display: page.page_type_display_name,
                    attributes: pageAttributes.attributes || {}
                });
            } else {
                console.error(`Error extracting page ${page.page_number}`);
                extractedPages.push({
                    page_number: page.page_number,
                    page_type: page.page_type_name,
                    page_type_display: page.page_type_display_name,
                    attributes: {},
                    error: 'Error al extraer atributos'
                });
            }
        }

        // Step 3: Build final JSON
        progressBar.style.width = '100%';
        progressText.textContent = '100%';
        progressStatus.textContent = 'Extracción completada!';

        extractedData = {
            provisional_document_id: currentProvisionalId,
            extracted_at: new Date().toISOString(),
            total_pages: totalPages,
            pages: extractedPages
        };

        // Display results
        displayResults(extractedData);

        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 1000);

    } catch (error) {
        console.error('Error:', error);
        showToast('Error durante la extracción: ' + error.message, 'error');
        progressDiv.style.display = 'none';
    }
}

// Display extraction results
function displayResults(data) {
    const resultsDiv = document.getElementById('extractionResults');
    const summaryDiv = document.getElementById('extractionSummary');
    const jsonOutput = document.getElementById('jsonOutput');

    // Summary
    const pageTypeCounts = {};
    let totalAttributes = 0;

    data.pages.forEach(page => {
        pageTypeCounts[page.page_type_display] = (pageTypeCounts[page.page_type_display] || 0) + 1;
        totalAttributes += Object.keys(page.attributes).length;
    });

    const summaryHtml = `
        <div class="alert alert-info">
            <strong>Total de páginas:</strong> ${data.total_pages}<br>
            <strong>Total de atributos extraídos:</strong> ${totalAttributes}<br>
            <strong>Tipos de páginas:</strong>
            <ul class="mb-0 mt-2">
                ${Object.entries(pageTypeCounts).map(([type, count]) =>
                    `<li>${type}: ${count} página(s)</li>`
                ).join('')}
            </ul>
        </div>
    `;

    summaryDiv.innerHTML = summaryHtml;

    // JSON output
    jsonOutput.textContent = JSON.stringify(data, null, 2);

    resultsDiv.style.display = 'block';
}

// Save extracted attributes to database
async function saveExtractedAttributes() {
    if (!extractedData || !currentProvisionalId) {
        showToast('No hay datos para guardar', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';

    try {
        const response = await fetch(`${API_BASE_URL}/provisional-documents/${currentProvisionalId}/save-extracted-attributes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(extractedData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al guardar atributos');
        }

        const result = await response.json();
        showToast('Atributos guardados exitosamente en la base de datos', 'success');

        saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Guardado';
        saveBtn.classList.remove('btn-success');
        saveBtn.classList.add('btn-secondary');

    } catch (error) {
        console.error('Error:', error);
        showToast('Error al guardar: ' + error.message, 'error');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-save"></i> Guardar en Base de Datos';
    }
}

// Download JSON file
function downloadJson() {
    if (!extractedData) {
        showToast('No hay datos para descargar', 'warning');
        return;
    }

    const jsonStr = JSON.stringify(extractedData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted_attributes_${currentProvisionalId}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('JSON descargado', 'success');
}
