// API Functions for Document Corrector

class DocumentAPI {
    // Commercial Documents
    static async uploadCommercialDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(getApiUrl('/documents/commercial'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error uploading document');
        }

        return await response.json();
    }

    static async listCommercialDocuments() {
        const response = await fetch(getApiUrl('/documents/commercial'));

        if (!response.ok) {
            throw new Error('Error fetching commercial documents');
        }

        return await response.json();
    }

    static async getCommercialDocument(id) {
        const response = await fetch(getApiUrl(`/documents/commercial/${id}`));

        if (!response.ok) {
            throw new Error('Error fetching document');
        }

        return await response.json();
    }

    static async deleteCommercialDocument(id) {
        const response = await fetch(getApiUrl(`/documents/commercial/${id}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting document');
        }

        return await response.json();
    }

    // Provisional Documents
    static async uploadProvisionalDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(getApiUrl('/documents/provisional'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error uploading document');
        }

        return await response.json();
    }

    static async listProvisionalDocuments() {
        const response = await fetch(getApiUrl('/documents/provisional'));

        if (!response.ok) {
            throw new Error('Error fetching provisional documents');
        }

        return await response.json();
    }

    static async getProvisionalDocument(id) {
        const response = await fetch(getApiUrl(`/documents/provisional/${id}`));

        if (!response.ok) {
            throw new Error('Error fetching document');
        }

        return await response.json();
    }

    static async deleteProvisionalDocument(id) {
        const response = await fetch(getApiUrl(`/documents/provisional/${id}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting document');
        }

        return await response.json();
    }

    // Comparisons
    static async createComparison(commercialDocId, provisionalDocId) {
        const response = await fetch(getApiUrl('/comparisons/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                commercial_document_id: commercialDocId,
                provisional_document_id: provisionalDocId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating comparison');
        }

        return await response.json();
    }

    static async batchCompare(provisionalDocId) {
        const response = await fetch(getApiUrl(`/comparisons/batch?provisional_document_id=${provisionalDocId}`), {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error in batch comparison');
        }

        return await response.json();
    }

    static async listComparisons(status = null) {
        let url = getApiUrl('/comparisons/');
        if (status) {
            url += `?status=${status}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Error fetching comparisons');
        }

        return await response.json();
    }

    static async getComparison(id) {
        const response = await fetch(getApiUrl(`/comparisons/${id}`));

        if (!response.ok) {
            throw new Error('Error fetching comparison');
        }

        return await response.json();
    }

    // Attributes
    static async createAttribute(attributeData) {
        const response = await fetch(getApiUrl('/attributes/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(attributeData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating attribute');
        }

        return await response.json();
    }

    static async listAttributes() {
        const response = await fetch(getApiUrl('/attributes/'));

        if (!response.ok) {
            throw new Error('Error fetching attributes');
        }

        return await response.json();
    }

    static async deleteAttribute(id) {
        const response = await fetch(getApiUrl(`/attributes/${id}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting attribute');
        }

        return await response.json();
    }

    static async createDefaultAttributes() {
        const response = await fetch(getApiUrl('/attributes/defaults'), {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error('Error creating default attributes');
        }

        return await response.json();
    }
}
