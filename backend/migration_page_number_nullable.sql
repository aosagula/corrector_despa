-- Migration: Drop page_number column from attribute_extraction_coordinates table
-- Reason: page_number is no longer needed since coordinates are associated with page_type_id

-- Drop the page_number column
ALTER TABLE attribute_extraction_coordinates
DROP COLUMN page_number;

-- Verify the change - this should show the table structure without page_number
DESCRIBE attribute_extraction_coordinates;
