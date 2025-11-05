-- Migration: Add data_type column to attribute_extraction_coordinates table
-- Reason: Store the data type (text, number, date) for each extraction coordinate

-- Add data_type column with default value 'text'
ALTER TABLE attribute_extraction_coordinates
ADD COLUMN data_type VARCHAR(20) DEFAULT 'text' AFTER description;

-- Update existing records to have 'text' as default
UPDATE attribute_extraction_coordinates
SET data_type = 'text'
WHERE data_type IS NULL;

-- Verify the change
DESCRIBE attribute_extraction_coordinates;
