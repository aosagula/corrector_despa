"""
Ejemplo de uso de la API de gestión de prompts

Este script demuestra cómo usar los endpoints de gestión de prompts
para personalizar la clasificación y extracción de datos.
"""

import requests
import json

# URL base de la API
BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, title):
    """Imprime una respuesta de la API de forma legible"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print()


def ejemplo_1_inicializar_prompts():
    """Ejemplo 1: Inicializar prompts por defecto"""
    print("\n### EJEMPLO 1: Inicializar Prompts por Defecto ###")

    response = requests.post(f"{BASE_URL}/prompts/initialize-defaults")
    print_response(response, "Inicialización de Prompts")


def ejemplo_2_listar_prompts():
    """Ejemplo 2: Listar todos los prompts"""
    print("\n### EJEMPLO 2: Listar Prompts ###")

    # Listar todos
    response = requests.get(f"{BASE_URL}/prompts/")
    print_response(response, "Todos los Prompts")

    # Listar solo prompts de clasificación activos
    response = requests.get(
        f"{BASE_URL}/prompts/",
        params={"prompt_type": "classification", "active_only": True}
    )
    print_response(response, "Prompts de Clasificación Activos")

    # Listar prompts de extracción
    response = requests.get(
        f"{BASE_URL}/prompts/",
        params={"prompt_type": "extraction", "active_only": True}
    )
    print_response(response, "Prompts de Extracción Activos")


def ejemplo_3_obtener_prompt_activo():
    """Ejemplo 3: Obtener prompts activos específicos"""
    print("\n### EJEMPLO 3: Obtener Prompts Activos ###")

    # Obtener prompt de clasificación activo
    response = requests.get(f"{BASE_URL}/prompts/classification/active")
    print_response(response, "Prompt de Clasificación Activo")

    # Obtener prompt de extracción para facturas
    response = requests.get(f"{BASE_URL}/prompts/extraction/factura/active")
    print_response(response, "Prompt de Extracción para Facturas")


def ejemplo_4_crear_prompt_personalizado():
    """Ejemplo 4: Crear un prompt personalizado"""
    print("\n### EJEMPLO 4: Crear Prompt Personalizado ###")

    # Crear un prompt de extracción personalizado para facturas
    nuevo_prompt = {
        "name": "extraction_factura_detallada",
        "prompt_type": "extraction",
        "document_type": "factura",
        "prompt_template": """Analiza esta factura y extrae la información de forma DETALLADA:

{text_content}

Extrae los siguientes campos en formato JSON:
{{
  "numero_factura": "...",
  "fecha_emision": "...",
  "fecha_vencimiento": "...",
  "proveedor": {{
    "nombre": "...",
    "cuit": "...",
    "direccion": "..."
  }},
  "cliente": {{
    "nombre": "...",
    "cuit": "...",
    "direccion": "..."
  }},
  "items": [
    {{
      "descripcion": "...",
      "cantidad": ...,
      "precio_unitario": ...,
      "subtotal": ...
    }}
  ],
  "subtotal": ...,
  "iva": ...,
  "total": ...,
  "moneda": "...",
  "condiciones_pago": "..."
}}

Si algún campo no está presente, usa null.""",
        "description": "Prompt detallado para extracción de facturas con información completa del proveedor y cliente",
        "is_active": 0,  # Crear inactivo primero para probar
        "variables": {
            "text_content": "Contenido de texto de la factura",
            "document_type": "factura"
        }
    }

    response = requests.post(f"{BASE_URL}/prompts/", json=nuevo_prompt)
    print_response(response, "Crear Prompt Personalizado")

    return response.json().get("id") if response.status_code == 200 else None


def ejemplo_5_actualizar_prompt(prompt_id):
    """Ejemplo 5: Actualizar un prompt existente"""
    print("\n### EJEMPLO 5: Actualizar Prompt ###")

    if not prompt_id:
        print("No hay prompt_id disponible. Ejecuta primero ejemplo_4.")
        return

    # Actualizar la descripción y activar el prompt
    actualizacion = {
        "description": "Prompt MEJORADO para extracción detallada de facturas",
        "is_active": 1
    }

    response = requests.put(f"{BASE_URL}/prompts/{prompt_id}", json=actualizacion)
    print_response(response, f"Actualizar Prompt ID {prompt_id}")


def ejemplo_6_obtener_prompt_por_nombre():
    """Ejemplo 6: Obtener un prompt por nombre"""
    print("\n### EJEMPLO 6: Obtener Prompt por Nombre ###")

    response = requests.get(f"{BASE_URL}/prompts/name/default_classification")
    print_response(response, "Obtener Prompt por Nombre")


def ejemplo_7_modificar_clasificacion():
    """Ejemplo 7: Modificar el prompt de clasificación"""
    print("\n### EJEMPLO 7: Modificar Prompt de Clasificación ###")

    # Primero obtener el prompt actual
    response = requests.get(f"{BASE_URL}/prompts/classification/active")
    if response.status_code != 200:
        print("No se pudo obtener el prompt de clasificación")
        return

    prompt_actual = response.json()
    prompt_id = prompt_actual["id"]

    # Modificar el prompt para incluir más categorías
    nuevo_template = """Analiza el siguiente contenido de documento y clasifícalo en una de estas categorías:
- factura
- orden_compra
- certificado_origen
- especificacion_tecnica
- contrato
- remito
- nota_credito
- nota_debito
- comprobante_pago
- otro

IMPORTANTE: Analiza cuidadosamente el contenido para determinar el tipo correcto.

Contenido del documento:
{text_content}

Responde ÚNICAMENTE con un JSON en el siguiente formato:
{{"document_type": "tipo_de_documento", "confidence": 0.95, "reasoning": "breve explicación del por qué de la clasificación"}}"""

    actualizacion = {
        "prompt_template": nuevo_template,
        "description": "Prompt de clasificación mejorado con más categorías de documentos"
    }

    response = requests.put(f"{BASE_URL}/prompts/{prompt_id}", json=actualizacion)
    print_response(response, "Modificar Prompt de Clasificación")


def ejemplo_completo():
    """Ejecuta todos los ejemplos en secuencia"""
    print("\n" + "="*60)
    print("EJEMPLOS DE GESTIÓN DE PROMPTS")
    print("="*60)

    # Ejemplo 1: Inicializar
    ejemplo_1_inicializar_prompts()

    # Ejemplo 2: Listar
    ejemplo_2_listar_prompts()

    # Ejemplo 3: Obtener activos
    ejemplo_3_obtener_prompt_activo()

    # Ejemplo 4: Crear personalizado
    nuevo_prompt_id = ejemplo_4_crear_prompt_personalizado()

    # Ejemplo 5: Actualizar
    ejemplo_5_actualizar_prompt(nuevo_prompt_id)

    # Ejemplo 6: Obtener por nombre
    ejemplo_6_obtener_prompt_por_nombre()

    # Ejemplo 7: Modificar clasificación
    ejemplo_7_modificar_clasificacion()

    print("\n" + "="*60)
    print("EJEMPLOS COMPLETADOS")
    print("="*60)


if __name__ == "__main__":
    # Ejecutar todos los ejemplos
    ejemplo_completo()

    # O ejecutar ejemplos individuales:
    # ejemplo_1_inicializar_prompts()
    # ejemplo_2_listar_prompts()
    # ejemplo_3_obtener_prompt_activo()
    # prompt_id = ejemplo_4_crear_prompt_personalizado()
    # ejemplo_5_actualizar_prompt(prompt_id)
    # ejemplo_6_obtener_prompt_por_nombre()
    # ejemplo_7_modificar_clasificacion()
