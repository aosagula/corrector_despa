-- Script para verificar y agregar la columna data_type si no existe

-- Verificar estructura actual de la tabla
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'attribute_extraction_coordinates'
ORDER BY ORDINAL_POSITION;

-- Si la columna data_type no aparece en el resultado anterior, ejecutar:
-- ALTER TABLE attribute_extraction_coordinates
-- ADD COLUMN data_type VARCHAR(20) DEFAULT 'text' AFTER description;
