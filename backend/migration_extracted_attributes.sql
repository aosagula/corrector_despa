-- Migration: Create extracted_attributes table
-- Reason: Store extracted attributes from provisional documents

CREATE TABLE IF NOT EXISTS extracted_attributes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provisional_document_id INT NOT NULL,
    extracted_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (provisional_document_id) REFERENCES provisional_documents(id) ON DELETE CASCADE,
    INDEX idx_provisional_document_id (provisional_document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verify the table was created
DESCRIBE extracted_attributes;
