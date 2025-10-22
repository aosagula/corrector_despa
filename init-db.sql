-- Inicialización de la base de datos
CREATE DATABASE IF NOT EXISTS corrector_despa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE corrector_despa;

-- Las tablas se crearán automáticamente por SQLAlchemy
-- Este archivo está aquí para cualquier configuración inicial adicional

-- Insertar atributos por defecto (opcional)
-- Los atributos se pueden crear a través de la API usando el endpoint /attributes/defaults
