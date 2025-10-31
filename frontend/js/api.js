// API Functions for Document Corrector

class DocumentAPI {
    // Commercial Documents
    static async uploadCommercialDocument(file, reference = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (reference) {
            formData.append('reference', reference);
        }

        const response = await fetch(getApiUrl('/documents/commercial'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Error uploading document';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                // Si no se puede parsear el JSON, usar el texto de la respuesta
                errorMessage = await response.text() || errorMessage;
            }
            throw new Error(errorMessage);
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
    static async uploadProvisionalDocument(file, reference = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (reference) {
            formData.append('reference', reference);
        }

        const response = await fetch(getApiUrl('/documents/provisional'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'Error uploading document';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                // Si no se puede parsear el JSON, usar el texto de la respuesta
                errorMessage = await response.text() || errorMessage;
            }
            throw new Error(errorMessage);
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

    // Prompts
    static async listPrompts(promptType = null, activeOnly = false) {
        let url = getApiUrl('/prompts/');
        const params = new URLSearchParams();

        if (promptType) {
            params.append('prompt_type', promptType);
        }
        if (activeOnly) {
            params.append('active_only', 'true');
        }

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Error fetching prompts');
        }

        return await response.json();
    }

    static async getPrompt(id) {
        const response = await fetch(getApiUrl(`/prompts/${id}`));

        if (!response.ok) {
            throw new Error('Error fetching prompt');
        }

        return await response.json();
    }

    static async getPromptByName(name) {
        const response = await fetch(getApiUrl(`/prompts/name/${name}`));

        if (!response.ok) {
            throw new Error('Error fetching prompt');
        }

        return await response.json();
    }

    static async getActiveClassificationPrompt() {
        const response = await fetch(getApiUrl('/prompts/classification/active'));

        if (!response.ok) {
            throw new Error('No active classification prompt found');
        }

        return await response.json();
    }

    static async getActiveExtractionPrompt(documentType) {
        const response = await fetch(getApiUrl(`/prompts/extraction/${documentType}/active`));

        if (!response.ok) {
            throw new Error(`No active extraction prompt found for ${documentType}`);
        }

        return await response.json();
    }

    static async createPrompt(promptData) {
        const response = await fetch(getApiUrl('/prompts/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promptData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating prompt');
        }

        return await response.json();
    }

    static async updatePrompt(id, promptData) {
        const response = await fetch(getApiUrl(`/prompts/${id}`), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promptData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error updating prompt');
        }

        return await response.json();
    }

    static async deletePrompt(id) {
        const response = await fetch(getApiUrl(`/prompts/${id}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting prompt');
        }

        return await response.json();
    }

    static async initializeDefaultPrompts() {
        const response = await fetch(getApiUrl('/prompts/initialize-defaults'), {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error initializing default prompts');
        }

        return await response.json();
    }

    // Provisional Document Images
    static async getProvisionalDocumentImages(documentId) {
        const response = await fetch(getApiUrl(`/documents/provisional/${documentId}/images`));

        if (!response.ok) {
            throw new Error('Error fetching document images');
        }

        return await response.json();
    }

    static getProvisionalDocumentImageUrl(documentId, pageNumber) {
        return getApiUrl(`/documents/provisional/${documentId}/images/${pageNumber}`);
    }

    static async detectProvisionalPages(documentId) {
        const response = await fetch(getApiUrl(`/documents/provisional/${documentId}/detect-pages`));

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al detectar páginas');
        }

        return await response.json();
    }

    // Coordinates
    static async createCoordinate(coordinateData) {
        const response = await fetch(getApiUrl('/coordinates/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(coordinateData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating coordinate');
        }

        return await response.json();
    }

    static async listCoordinates(attributeId = null, pageNumber = null) {
        let url = getApiUrl('/coordinates/');
        const params = new URLSearchParams();

        if (attributeId) {
            params.append('attribute_id', attributeId);
        }
        if (pageNumber) {
            params.append('page_number', pageNumber);
        }

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Error fetching coordinates');
        }

        return await response.json();
    }

    static async updateCoordinate(coordinateId, coordinateData) {
        const response = await fetch(getApiUrl(`/coordinates/${coordinateId}`), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(coordinateData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error updating coordinate');
        }

        return await response.json();
    }

    static async deleteCoordinate(coordinateId) {
        const response = await fetch(getApiUrl(`/coordinates/${coordinateId}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting coordinate');
        }

        return await response.json();
    }

    static async extractDataByCoordinates(documentId) {
        const response = await fetch(getApiUrl(`/coordinates/extract/${documentId}`), {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error extracting data');
        }

        return await response.json();
    }

    // Page Types
    static async createPageType(pageTypeData) {
        const response = await fetch(getApiUrl('/page-types/'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(pageTypeData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating page type');
        }

        return await response.json();
    }

    static async listPageTypes() {
        const response = await fetch(getApiUrl('/page-types/'));

        if (!response.ok) {
            throw new Error('Error fetching page types');
        }

        return await response.json();
    }

    static async getPageType(pageTypeId) {
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}`));

        if (!response.ok) {
            throw new Error('Error fetching page type');
        }

        return await response.json();
    }

    static async updatePageType(pageTypeId, pageTypeData) {
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}`), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(pageTypeData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error updating page type');
        }

        return await response.json();
    }

    static async deletePageType(pageTypeId) {
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting page type');
        }

        return await response.json();
    }

    // Detection Rules
    static async createDetectionRule(pageTypeId, ruleData) {
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}/rules`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error creating detection rule');
        }

        return await response.json();
    }

    static async listDetectionRules(pageTypeId) {
        const response = await fetch(getApiUrl(`/page-types/${pageTypeId}/rules`));

        if (!response.ok) {
            throw new Error('Error fetching detection rules');
        }

        return await response.json();
    }

    static async updateDetectionRule(ruleId, ruleData) {
        const response = await fetch(getApiUrl(`/page-types/rules/${ruleId}`), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error updating detection rule');
        }

        return await response.json();
    }

    static async deleteDetectionRule(ruleId) {
        const response = await fetch(getApiUrl(`/page-types/rules/${ruleId}`), {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error deleting detection rule');
        }

        return await response.json();
    }
}
