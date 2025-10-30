"""
Script de migración para agregar columna extraction_model a las tablas de documentos
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Agrega la columna extraction_model a las tablas commercial_documents y provisional_documents"""

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        try:
            # Agregar columna extraction_model a commercial_documents
            print("Agregando columna extraction_model a commercial_documents...")
            conn.execute(text(
                "ALTER TABLE commercial_documents ADD COLUMN extraction_model VARCHAR(100)"
            ))
            conn.commit()
            print("✓ Columna extraction_model agregada a commercial_documents")
        except Exception as e:
            print(f"Error en commercial_documents (puede que ya exista): {e}")

        try:
            # Agregar columna extraction_model a provisional_documents
            print("Agregando columna extraction_model a provisional_documents...")
            conn.execute(text(
                "ALTER TABLE provisional_documents ADD COLUMN extraction_model VARCHAR(100)"
            ))
            conn.commit()
            print("✓ Columna extraction_model agregada a provisional_documents")
        except Exception as e:
            print(f"Error en provisional_documents (puede que ya exista): {e}")

    print("\nMigración completada!")
    print("Los documentos futuros guardarán el modelo usado para extracción.")

if __name__ == "__main__":
    migrate()
